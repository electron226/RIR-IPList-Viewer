#/usr/bin/python
# vim: set fileencoding=utf-8
import sys
import re
import os
import urllib2
import shutil
import hashlib
import logging

from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp import template

from google.appengine import runtime
from google.appengine.runtime import apiproxy_errors
try:
    from google3.apphosting.runtime import _apphosting_runtime___python__apiproxy
except ImportError:
    _apphosting_runtime__python__apiproxy = None

# 取得先
RIR = {
        'ARIN':'http://ftp.apnic.net/stats/arin/delegated-arin-latest',
        'APNIC':'http://ftp.apnic.net/stats/apnic/delegated-apnic-latest',
        'RIPE':'http://ftp.apnic.net/stats/ripe-ncc/delegated-ripencc-latest',
        'LACNIC':'http://ftp.apnic.net/stats/lacnic/delegated-lacnic-latest',
        'AFRINIC':'http://ftp.apnic.net/stats/afrinic/delegated-afrinic-latest'
        }

# IPアドレス範囲を格納するクラス
# start : 数値化した開始IP
# end : 数値化した終了IP(実際の最後のIPはこの数値の-1)
# StartIP : 開始IP(文字列)を返すメソッド
# EndIP : 終了IP(文字列)を返すメソッド
class IP:
    # 初期化
    # xxx.xxx.xxx.xxx
    # ip1.ip2.ip3.ip4
    # value : 割当数
    def __init__(self, ip1, ip2, ip3, ip4, value):
        self.start = (int(ip1) << 24) + (int(ip2) << 16) + (int(ip3) << 8) + int(ip4)
        self.end = self.start + int(value)

    # 与えられた値をIPに変換
    def __convert__(self, value):
        return '%d.%d.%d.%d' % ((value & 0xFF000000) >> 24, (value & 0x00FF0000) >> 16,
                (value & 0x0000FF00) >> 8, (value & 0x000000FF))
    
    # 開始IPを文字列で返す
    def StartIP(self):
        return self.__convert__(self.end - 1)

    # 終了IPを文字列で返す
    def EndIP(self):
        return self.__convert__(self.end - 1)

class Version(db.Model):
    registry = db.StringProperty()
    hash = db.StringProperty()

class IPTable(db.Model):
    registry = db.StringProperty()
    cc = db.StringProperty()
    start = db.StringProperty()
    value = db.IntegerProperty()

class ARIN(IPTable): pass
class APNIC(IPTable): pass
class RIPE(IPTable): pass
class LACNIC(IPTable): pass
class AFRINIC(IPTable): pass

def Clear(nic_class):
    db.delete(nic_class.all())

def AllClear():
    Clear(ARIN)
    Clear(APNIC)
    Clear(RIPE)
    Clear(LACNIC)
    Clear(AFRINIC)
    Clear(Version)

# IPリストをダウンロードするクラス
class IPList():
    # ハッシュ値確認用
    header_rule = re.compile(r'\d{1}\|[a-z]+\|\d+\|\d+\|\d+\|\d+\|[+-]?\d+')

    # レコード用
    # xxx.xxx.xxx.xxx
    #  G2  G3  G4  G5
    # G1 = 国コード, G6 = 範囲
    record_rule = re.compile(r'([A-Z]{2})\|ipv4\|(\d+).(\d+).(\d+).(\d+)\|(\d+)') # IPv4
    
    # 与えたURLのIP割当ファイルの更新を確認し、取得してデータベースに登録
    # nic : 更新するregistryの名前
    def retrieve(self, nic):
        nic_class = globals()[nic] # クラス名からクラスオブジェクトを取得

        url = RIR[nic]
        try:
            f = urllib2.urlopen(url)
        except urllib2.URLError:
            logging.error('エラー: "%s" が開けません。' % url)
            return False

        # 前回のハッシュ値と取得先のハッシュ値を比較
        get = True
        newhash = None
        vtable = Version.all()
        vtable.filter('registry =', nic)
        vresult = vtable.fetch(1)
        if vresult:
            oldhash = vresult[0].hash
        else:
            oldhash = None

        while True:
            line = f.readline()
            if not line:
                break
            header = self.header_rule.match(line)
            if header:
                newhash = hashlib.md5(header.group()).hexdigest()
                if oldhash != None and oldhash == newhash:
                    get = False
                    logging.info('既に最新版です。')
                break

        if get:
            logging.info('ダウンロードを開始します。')

            if not newhash:
                logging.error('取得先のIP割り当てファイルのヘッダが見つかりません。')
                return False

            # 一致するリストを一度全て削除
            # Clear(nic_class)
            db.delete(nic_class.all())

            # リストをデータベースに登録
            iptableobj = []
            for line in f.readlines():
                record = self.record_rule.search(line)
                if record:
                    StartIP = '%s.%s.%s.%s' % (record.group(2), record.group(3), record.group(4), record.group(5))
                    iptable = nic_class(
                            registry = nic,
                            cc = record.group(1),
                            start = StartIP,
                            value = int(record.group(6)));
                    iptableobj.append(iptable)
            db.put(iptableobj)

            # ハッシュ更新
            if vresult:
                vtable = vresult[0]
                vtable.hash = newhash
            else:
                vtable = Version(
                        registry = nic,
                        hash = newhash);
            db.put(vtable)

            logging.info('ダウンロードを完了。')
            return True

        return False

class CronHandler(webapp.RequestHandler):
    def get(self):
        # 最新のリストを取得
        list = IPList()
        for nic in RIR.keys():
            logging.info('"%s" の更新を開始。' % nic)
            try:
                list.retrieve(nic)
            except runtime.DeadlineExceededError:
                logging.error('"%s"の取得に失敗' % nic)

        # 終了処理
        logging.info('完了しました。')

class MainHandler(webapp.RequestHandler):
    def get(self):
        # クライアントのJavaScriptで処理をやればよくね？
        # ファイルを保存 -> アクセスされる -> ダウンロードさせて処理
        pass

def main():
    application = webapp.WSGIApplication([('/', MainHandler), ('/cron', CronHandler)], debug = True)
    util.run_wsgi_app(application)

### Main ###
if __name__ == '__main__':
    main()
