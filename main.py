#/usr/bin/python
# vim: set fileencoding=utf-8
import sys
import re
import os
import urllib2
import shutil
import hashlib
import logging

from google.appengine.api import memcache
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

# デフォルトの国コード、国名が記述されたファイル
countries_code = ('countries_code.txt')

####################################################
# ここから先は基本的に設定不要
####################################################

# 対応済みの出力リスト形式
support = ('PG', 'ED', 'SH')

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
# StartIP : 開始IP(文字列)
# EndIP : 終了IP(文字列)を返すメソッド
class IP:
    # 初期化
    # ip : IPアドレスの文字列
    # value : 割当数
    def Init(self, ip, value):
        ip = ip.split('.')
        self.Init(ip[0], ip[1], ip[2], ip[3], value)

    # 初期化
    # xxx.xxx.xxx.xxx
    # ip1.ip2.ip3.ip4
    # value : 割当数
    def Init(self, ip1, ip2, ip3, ip4, value):
        self.start = (int(ip1) << 24) + (int(ip2) << 16) + (int(ip3) << 8) + int(ip4)
        self.end = self.start + int(value)
        self.StartIP = '%s.%s.%s.%s' % (ip1, ip2, ip3, ip4)

    # 終了IPを文字列で返す
    def EndIP(self):
        last = self.end - 1
        return '%d.%d.%d.%d' % ((last & 0xFF000000) >> 24, (last & 0x00FF0000) >> 16,
                (last & 0x0000FF00) >> 8, (last & 0x000000FF))

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
    iptable = nic_class.all()
    while True:
        ip = iptable.fetch(1000)
        if ip:
            db.delete(ip)
        else:
            break

def AllClear():
    Clear(ARIN)
    Clear(APNIC)
    Clear(RIPE)
    Clear(LACNIC)
    Clear(AFRINIC)

    vtable = Version.all()
    while True:
        v = vtable.fetch(10)
        if v:
            db.delete(v)
        else:
            break

def get_cache(key, key_prefix = '', namespace = None):
    if isinstance(key, list):
        return memcache.get_multi(key, key_prefix, namespace)
    else:
        result = memcache.get(key, namespace)
        return { key : result }

def add_cache(key, value = None, time = 0, key_prefix = '', min_compress_len = 0, namespace = None):
    if isinstance(key, list):
        misslist = memcache.add_multi(key, time, key_prefix, min_compress_len, namespace)
        if len(misslist) != 0:
            logging.error("Memcache add_multi Failure.")
            for miss in misslist:
                logging.error("\n\t%s" % miss)
    else:
        if not memcache.add(key, value, time, min_compress_len, namespace):
            logging.error("Memcache add %s Failure." % key)

def set_cache(key, value = None, time = 0, key_prefix = '', min_compress_len = 0, namespace = None):
    if isinstance(key, list):
        misslist = memcache.set_multi(key, time, key_prefix, min_compress_len, namespace)
        if len(misslist) != 0:
            logging.error("Memcache set_multi Failure.")
            for miss in misslist:
                logging.error("\n\t%s" % miss)
    else:
        if not memcache.set(key, value, time, min_compress_len, namespace):
            logging.error("Memcache set %s Failure." % key)

def replace_cache(key, value = None, time = 0, key_prefix = '', min_compress_len = 0, namespace = None):
    addflag = False
    if isinstance(key, list):
        misslist = memcache.replace_multi(key, time, key_prefix, min_compress_len, namespace)
        count = len(misslist)
        if count == len(key):
            logging.error("Memcache replace_multi All Failure.")
            addflag = True
        elif count != 0:
            logging.error("Memcache replace_multi Failure.")
            for miss in misslist:
                logging.error("\n\t%s" % miss)
    else:
        if not memcache.replace(key, value, time, min_compress_len, namespace):
            logging.error("Memcache replace Failure.")
            addflag = True

    if addflag:
        logging.info("Memcache add process Start.")
        add_cache(key, value, time, key_prefix, min_compress_len, namespace)

def delete_cache(key, seconds = 0, key_prefix = '', namespace = None):
    if isinstance(key, list):
        if not memcache.delete_multi(key, seconds, key_prefix, namespace):
            logging.error("Memcache delete_multi Failure.")
    else:
        result = memcache.delete(key, seconds, namespace)
        if result == 0:
            logging.error("Memcache delete %s Failure." % key)
        elif result == 1:
            logging.warning("Memcache delete %s Missing." % key)

"""
# デフォルトの国コード、国名を読み込み、連想配列を返す
def LoadCountries():
    # デフォルトの国リストを読み込む
    try:
        def_code = open(countries_code, 'r') 
    except IOError:
        sys.exit('エラー: デフォルトの国コード・国名が記述されたファイル "%s" が開けません。' % countries_code)

    # 読み込んだ国名コードと国名で連想配列を作成
    countries_data = {}
    for line in def_code.readlines():
        str = line.rstrip('\n')
        code = str.split(':')
        countries_data.update({code[0]:code[1]})
    def_code.close()

    return countries_data
"""

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
        vtable = db.GqlQuery("SELECT * FROM Version WHERE registry = '%s'" % nic)
        newhash = None
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

            # リストをデータベースに登録
            iptableobj = []
            for line in f.readlines():
                record = self.record_rule.search(line)
                if record:
                    ipobj = IP()
                    ipobj.Init(record.group(2), record.group(3), record.group(4), record.group(5), record.group(6))
                    iptableobj.append(ipobj)
                    """
                    StartIP = '%s.%s.%s.%s' % (record.group(2), record.group(3), record.group(4), record.group(5))
                    iptable = nic_class(
                            registry = nic,
                            cc = record.group(1),
                            start = StartIP,
                            value = int(record.group(6)));
                    iptableobj.append(iptable)
            db.put(iptableobj)
                    """

            # キャッシュ置き換え
            replace_cache(nic, iptableobj)

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

    # 最適化
    def Combine(self):
        for lang in self.IPListLangs.keys():
            # 先にソートする
            self.IPListLangs[lang].sort(lambda x, y: cmp(x.start, y.start))

            SaveAddress = None
            for i in xrange(len(self.IPListLangs[lang]) - 1):
                IPList = self.IPListLangs[lang]
                # 現在のIP範囲の末尾と次のIP範囲の開始が同じ
                if IPList[i].end == IPList[i + 1].start:
                    if not SaveAddress:
                        # まだ結合されていないIP範囲
                        SaveAddress = i
                        IPList[i].end = IPList[i + 1].end
                        IPList[i + 1].start = None
                    else:
                        # 以前に結合したことがあるIP範囲
                        IPList[SaveAddress].end = IPList[i + 1].end
                        IPList[i + 1].start = None
                else:
                    SaveAddress = None

    # データベースからIPリストをファイルに出力
    # countries : key = 国名コード, value = 国名の連想配列
    # out_file : 出力ファイル名
    # type : 出力するリスト形式
    def Write(self, countries, out_file, type):
        try:
            output = open(out_file, 'w+b')
        except IOError:
            print 'エラー: "%s" が開けません。' % out_file
            return False

        # 最適化したリストを取得
        IPListLangs = self.Combine(countries.keys())

        # 一時ファイル作成
        temp = tempfile.TemporaryFile()

        if type == 'PG': # PeerBlock(PeerGuardian)形式
            for lang, country in countries.iteritems():
                for ipobj in IPListLangs[lang]:
                    if ipobj.start:
                        record = '%s:%s-%s' % (country, ipobj.StartIP, ipobj.EndIP())
                        temp.write(record + '\n')
        elif type == 'ED': # eDonkey形式
            for lang, country in countries.iteritems():
                for ipobj in IPListLangs[lang]:
                    if ipobj.start:
                        record = '%s - %s , 000 , %s' % (ipobj.StartIP, ipobj.EndIP(), country)
                        temp.write(record + '\n')
        elif type == 'SH': # Shareaza形式
            temp.write('<?xml version="1.0"?>\n')
            temp.write('\t<security xmlns="http://www.shareaza.com/schemas/Security.xsd">\n')
            for lang, country in countries.iteritems():
                for ipobj in IPListLangs[lang]:
                    if ipobj.start:
                        record = '<rule address="%s" action="deny" type="address" mask="%s" comment="%s"/>' \
                                % (ipobj.StartIP, ipobj.EndIP(), country)
                        temp.write('\t\t' + record + '\n')
            temp.write('\t</security>')
        else: # 未対応
            raise ValueError, 'エラー: 出力リスト形式 "%s" は未対応です。' % type

        # 書き込み
        temp.seek(0)
        shutil.copyfileobj(temp, output)

        output.close()
        return True

class CronHandler(webapp.RequestHandler):
    def get(self):
        #countries_data = LoadCountries()

        # 最新のリストを取得
        list = IPList()
        list.retrieve("AFRINIC")
        """
        for nic in RIR.keys():
            logging.info('"%s" の更新を開始。' % nic)
            try:
                list.retrieve(nic)
            except runtime.DeadlineExceededError:
                logging.error('"%s"の取得に失敗' % nic)

        # リスト作成処理
        logging.info('%s形式でリストを作成します。' % options.type)
        logging.info('IPリストの出力開始。')
        list.Write(countries_data, options.output, options.type)
        logging.info('IPリストの出力完了。')

        # 終了処理
        logging.info('完了しました。')
        """

class MainHandler(webapp.RequestHandler):
    def get(self):
        record = get_cache("AFRINIC")

        template_values = {
                'iptable': record["AFRINIC"]
                }
        path = os.path.join(os.path.dirname(__file__), 'main.html')
        self.response.out.write(template.render(path, template_values))

def main():
    application = webapp.WSGIApplication([('/', MainHandler), ('/cron', CronHandler)], debug = True)
    util.run_wsgi_app(application)

### Main ###
if __name__ == '__main__':
    main()
