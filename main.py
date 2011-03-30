#/usr/bin/python
# vim: set fileencoding=utf-8
import sys
import re
import os
import time
import hashlib
import logging
import zlib

import memcache_extra

from google.appengine.api import taskqueue
from google.appengine.api import urlfetch
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

# 設定
program_title = "RIR List Viewer"
program_version = "1.0"

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
        return self.__convert__(self.start)

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

class Countries(db.Model):
    cc = db.StringProperty()
    registry = db.StringProperty()

def Clear(nic_class):
    db.delete(nic_class.all())

def ClearFor(nic_class):
    table = nic_class.all()
    while True:
        records = table.fetch(1000)
        if records:
            db.delete(records)
        else:
            break

def AllClear():
    ClearFor(ARIN)
    ClearFor(APNIC)
    ClearFor(RIPE)
    ClearFor(LACNIC)
    ClearFor(AFRINIC)
    ClearFor(Version)

def CRC32Check(string):
    return zlib.crc32(string) & 0xFFFFFFFF

# IPリストをダウンロードするクラス
class IPList():
    # 取得したデータをzlib圧縮してmemcacheに保存
    def handle_urlfetch(self, rpc, nic):
        logging.info('Start "%s".' % nic)
        try:
            result = rpc.get_result()
            if result.status_code != 200:
                logging.error('Failed to open "%s".' % nic)
                return False
            cache_data = {
                    'data': zlib.compress(result.content), 
                    'crc': CRC32Check(result.content)}
            memcache_extra.replace_cache(nic, cache_data)
        except urlfetch.DownloadError:
            logging.error('Get "%s" failure.' % nic)
        except zlib.error:
            logging.error('Get "%s" failure. zlib Compress Error.' % nic)

    # コールバック関数
    def create_callback(self, rpc, nic):
        return lambda: self.handle_urlfetch(rpc, nic)
    
    # 与えたURLのIP割当ファイルの更新を確認し、取得してデータベースに登録
    # nics : 更新するregistryの名前のリスト
    def retrieve(self, nics):
        # urlfetchで非同期接続
        rpcs = []
        for nic in nics:
            rpc = urlfetch.create_rpc(deadline = 60)
            rpc.callback = self.create_callback(rpc, nic)
            urlfetch.make_fetch_call(rpc, RIR[nic]) #URLフェッチ開始
            rpcs.append(rpc)

        for rpc in rpcs:
            rpc.wait() # 完了まで待機、コールバック関数を呼び出す

        # タスクキューで処理させる
        datastore_task = taskqueue.Queue('datastore')
        for nic in nics:
            task = taskqueue.Task(url = '/datastore', params = {'registry': nic})
            datastore_task.add(task)
        return

class DataStore(webapp.RequestHandler):
    # ハッシュ値確認用
    header_rule = re.compile(r'\d{1}\|[a-z]+\|\d+\|\d+\|\d+\|\d+\|[+-]?\d+')

    # レコード用
    # xxx.xxx.xxx.xxx
    #  G2  G3  G4  G5
    # G1 = 国コード, G6 = 範囲
    record_rule = re.compile(r'([A-Z]{2})\|ipv4\|(\d+).(\d+).(\d+).(\d+)\|(\d+)') # IPv4

    def post(self):
        registry = self.request.get('registry')
        nic_class = globals()[registry]

        try:
            cache = memcache_extra.get_cache(registry)[registry]
            data = cache['data']
            crc = cache['crc']
            content = zlib.decompress(data)
            if CRC32Check(content) != crc:
                logging.error('memcache "%s" be damaged.' % registry)
                return False
        except TypeError, te:
            logging.error(te)
        except zlib.error:
            logging.error('zlib Decompress Error.' % registry)
            return False

        contents = content.split('\n')

        # 前回のハッシュを取得
        vtable = Version.all()
        vtable.filter('registry =', registry)
        vresult = vtable.fetch(1)
        if vresult:
            oldhash = vresult[0].hash
        else:
            oldhash = None

        # 前回のハッシュと今回のハッシュを比較
        get = True
        newhash = None
        for line in contents:
            header = self.header_rule.match(line)
            if header:
                newhash = hashlib.md5(header.group()).hexdigest()
                if oldhash != None and oldhash == newhash:
                    get = False
                    logging.info('Already Latest Edition the "%s".' % registry)
                break

        if not newhash:
            logging.error('Search the header of "%s".' % registry)
            return False

        if get:
            logging.info('Start update the "%s".' % registry)

            # 一致するリストを一度全て削除
            Clear(nic_class)

            # リストをデータストアに登録
            datastore_task = taskqueue.Queue('datastore')
            records = ""
            countries = set() # 国名リスト 
            count = 0
            for line in contents:
                record = self.record_rule.search(line)
                if record:
                    StartIP = '%s.%s.%s.%s' % (record.group(2), record.group(3), record.group(4), record.group(5))
                    records += "%s %s %s %s " % (registry, record.group(1), StartIP, record.group(6))
                    countries.add(record.group(1))
                    count += 1
                    # 一定量たまったらタスクキューで処理
                    if count > 150:
                        task = taskqueue.Task(url = '/datastore_put', params = {'records': records})
                        datastore_task.add(task)
                        records = ""
                        count = 0
            # 残った分をタスクキューで処理
            task = taskqueue.Task(url = '/datastore_put', params = {'records': records})
            datastore_task.add(task)

            # 国名をデータストアに保存
            ctablelist = []
            for country in countries:
                ctable = Countries(cc = country, registry = registry)
                ctablelist.append(ctable)
            db.put(ctablelist)

            # ハッシュ更新
            if vresult:
                vtable = vresult[0]
                vtable.hash = newhash
            else:
                vtable = Version(
                        registry = registry,
                        hash = newhash);
            db.put(vtable)

            logging.info('Update complete the "%s".' % registry)

class DataStorePut(webapp.RequestHandler):
    def post(self):
        records = self.request.get('records').rstrip()
        recordlist = records.split()
        recordcount = len(recordlist)
        if recordcount == 0:
            return False

        count = 0
        while count < recordcount:
            nic_class = globals()[recordlist[count]]
            ipobj = nic_class(
                    registry = recordlist[count], 
                    cc = recordlist[count + 1], 
                    start = recordlist[count + 2], 
                    value = int(recordlist[count + 3]))
            ipobj.put()
            count += 4

class CronHandler(webapp.RequestHandler):
    def get(self):
        try:
            list = IPList()
            list.retrieve(RIR.keys())
        except runtime.DeadlineExceededError:
            logging.error('Get "%s" failure.' % nic)

        # 終了処理
        logging.info('List Update Complete.')

class MainHandler(webapp.RequestHandler):
    # レコード用
    # xxx.xxx.xxx.xxx
    #  G2  G3  G4  G5
    # G1 = 国コード, G6 = 範囲
    record_rule = re.compile(r'([A-Z]{2})\|ipv4\|(\d+).(\d+).(\d+).(\d+)\|(\d+)') # IPv4

    def get(self):
        template_values = {
                'title': program_title,
                'version': program_version
                }
        path = os.path.join(os.path.dirname(__file__), 'main.html')
        self.response.out.write(template.render(path, template_values))

def main():
    application = webapp.WSGIApplication([
        ('/', MainHandler),
        ('/cron', CronHandler),
        ('/datastore', DataStore),
        ('/datastore_put', DataStorePut)],
        debug = True)
    util.run_wsgi_app(application)

### Main ###
if __name__ == '__main__':
    main()
