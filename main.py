#/usr/bin/python
# vim: set fileencoding=utf-8
import sys
import re
import os
import time
import hashlib
import logging
import zlib

from google.appengine.api import taskqueue
from google.appengine.api import urlfetch
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
        self.value = int(value)
        self.end = self.start + self.value 

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

class IPTable():
    def __init__(self, registry, cc, ip):
        self.registry = registry
        self.cc = cc
        self.ip = ip

class Countries():
    def __init__(self, cc, registry):
        self.cc = cc
        self.registry = registry

def Clear(registry, count = 0):
    while True:
        result = memcache.delete('%s_%d' % (registry, count))
        if result != 2:
            break

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
            if not memcache.set(nic, cache_data):
                logging.error('Set memcache, %s content failure.' % nic)
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

        try:
            cache = memcache.get(registry)
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

        try:
            contents = content.split('\n')
        except UnboundLocalError, ule:
            logging.error('%s' % ule)
            return False

        # 前回のハッシュを取得
        oldhash = memcache.get('%s_hash' % registry)
        if oldhash:
            logging.info('Get %s_hash Successs.' % registry)
        else:
            logging.info('Get %s_hash Failure.' % registry)

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

            # 一致するレジストリのキャッシュを削除
            Clear(registry)

            # 取得したリストをキャッシュに保存
            count = 0
            cache_count = 0
            countries = set() # 国名リスト 
            iplist = []
            for line in contents:
                record = self.record_rule.search(line)
                if record:
                    ipobj = IP(record.group(2), record.group(3), record.group(4), record.group(5), record.group(6))
                    ip = IPTable(registry, record.group(1), ipobj)
                    iplist.append(ip)

                    countries.add(record.group(1))
                    count += 1
                    # 一定量たまったらキャッシュに保存
                    if count > 1000:
                        if not memcache.set('%s_%d' % (registry, cache_count), iplist):
                            logging.error('Set recordlist failure. "%s_%d"' % (registry, cache_count))
                        else:
                            cache_count += 1
                        iplist = []
                        count = 0
            # 残った分をキャッシュに保存
            if len(iplist) != 0:
                if not memcache.set('%s_%d' % (registry, cache_count), iplist):
                    logging.error('Set iplist failure. "%s_%d"' % (registry, cache_count))

            # 国名リストをキャッシュに保存
            ctablelist = []
            for country in countries:
                ctable = Countries(cc = country, registry = registry)
                ctablelist.append(ctable)
            if not memcache.set('%s_countries' % registry, ctablelist):
                logging.error('Set ctablelist failure. "%s_countries"' % registry)

            # ハッシュ更新
            if memcache.set('%s_hash' % registry, newhash):
                logging.error('Set %s_hash Success.' % registry)
            else:
                logging.error('Set %s_hash Failure.' % registry)

            logging.info('Update complete the "%s".' % registry)

class CronHandler(webapp.RequestHandler):
    def get(self):
        try:
            list = IPList()
            list.retrieve(RIR.keys())
        except runtime.DeadlineExceededError:
            logging.error('Get "%s" failure.' % nic)

        """
        count = 0
        line = 0
        registry = 'AFRINIC'
        while True:
            cache = memcache.get('%s_%d' % (registry, count))
            if not cache:
                break

            for ipobj in cache:
                self.response.out.write('%s:\t%s<br />' % (line, ipobj.ip.StartIP()))
                line += 1
            count += 1
        """

        # 終了処理
        logging.info('List Update Complete.')

class MainHandler(webapp.RequestHandler):
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
        ('/datastore', DataStore)],
        debug = True)
    util.run_wsgi_app(application)

### Main ###
if __name__ == '__main__':
    main()
