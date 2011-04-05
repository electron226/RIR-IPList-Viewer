#/usr/bin/python
# vim: set fileencoding=utf-8
import sys
import re
import os
import time
import hashlib
import logging
import pickle
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
program_version = "1.1"

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

class CacheStore(db.Model):
    name = db.StringProperty(required = True)
    cache = db.BlobProperty()

class IPTable():
    def __init__(self, registry, cc, ip):
        self.registry = registry
        self.cc = cc
        self.ip = ip

class Countries():
    def __init__(self, cc, registry):
        self.cc = cc
        self.registry = registry

def get_cache(name):
    # memcacheから取得
    cache = memcache.get(name)
    if cache:
        logging.debug('Get cache success. "%s"' % name)
        return cache
    else:
        logging.debug('Get cache failure. "%s"' % name)

        # データストア内のキャッシュから取得
        logging.info('Get DataStore "CacheStore" start. "%s"' % name)
        query = db.GqlQuery("SELECT * FROM CacheStore WHERE name = :1", name)
        record = query.get()
        if record:
            logging.debug('Get Datastore "CacheStore" success. "%s"' % name)

            # memcache内に保存し直しておく
            storecache = pickle.loads(record.cache)
            if memcache.set(name, storecache):
                logging.debug('Set cache success. "%s"' % name)
            else:
                logging.error('Set cache failure. "%s"' % name)
            return storecache
        else:
            logging.error('Get Datastore "CacheStore" failure. "%s"' % name)
            return None

def set_cache(name, value):
    # memcacheに保存
    if memcache.set(name, value):
        logging.debug('Set cache success. "%s"' % name)

        # データストアにキャッシュを保存
        logging.info('Set Datastore "CacheStore" start. "%s"' % name)
        store = CacheStore(
                name = name, 
                cache = pickle.dumps(value, pickle.HIGHEST_PROTOCOL))
        store.put()
        logging.debug('Set Datastore "CacheStore" success. "%s"' % name)
        return True
    else:
        logging.error('Set cache failure. "%s"' % name)
        return False

def Clear(registry, default_count = 0):
    logging.info('DataStore"CacheStore" cache clear start.')
    # データストアキャッシュの削除
    count = default_count
    del_record = []
    while True:
        query = db.GqlQuery("SELECT * FROM CacheStore WHERE name = :1", '%s_%d' % (registry, count))
        record = query.get()
        if not record:
            if del_record:
                db.delete(del_record)
            break
        del_record.append(record)
        count += 1
    # 国名のデータストアキャッシュの削除
    query = db.GqlQuery("SELECT * FROM CacheStore WHERE name = :1", '%s_COUNTRIES' % registry)
    record = query.get()
    if record:
        record.delete()

    # キャッシュの削除
    logging.info('Cache clear start.')
    count = default_count
    while True:
        result = memcache.delete('%s_%d' % (registry, count))
        if result != 2:
            break
        count += 1
    # 国名のキャッシュの削除
    result = memcache.delete('%s_COUNTRIES' % registry)
    logging.info('Cache clear end.')

def ClearAll():
    logging.info('Cache all clear start.')
    if not memcache.flush_all():
        logging.error('memcache flush_all failure.')
    db.delete(CacheStore.all())
    logging.info('Cache all clear end.')

def CRC32Check(string):
    return zlib.crc32(string) & 0xFFFFFFFF

# IPリストをダウンロードするクラス
class IPList():
    # 取得したデータをzlib圧縮してmemcacheに保存
    def handle_urlfetch(self, rpc, registry):
        logging.info('Start "%s".' % registry)
        try:
            result = rpc.get_result()
            if result.status_code != 200:
                logging.error('Failed to open "%s".' % registry)
                return False

            cache_data = {
                    'data': zlib.compress(result.content), 
                    'crc': CRC32Check(result.content)}
            if not memcache.set(registry, cache_data):
                logging.error('Set memcache, %s content failure.' % registry)
        except urlfetch.DownloadError:
            logging.error('Get "%s" failure.' % registry)
        except zlib.error:
            logging.error('Get "%s" failure. zlib Compress Error.' % registry)

    # コールバック関数
    def create_callback(self, rpc, registry):
        return lambda: self.handle_urlfetch(rpc, registry)
    
    # 与えたURLのIP割当ファイルの更新を確認し、取得してデータベースに登録
    # registrys : 更新するregistryの名前のリスト
    def retrieve(self, registrys):
        # urlfetchで非同期接続
        rpcs = []
        for registry in registrys:
            rpc = urlfetch.create_rpc(deadline = 30)
            rpc.callback = self.create_callback(rpc, registry)
            urlfetch.make_fetch_call(rpc, RIR[registry]) #URLフェッチ開始
            rpcs.append(rpc)

        for rpc in rpcs:
            rpc.wait() # 完了まで待機、コールバック関数を呼び出す

        # タスクキューで処理させる
        datastore_task = taskqueue.Queue('datastore')
        for registry in registrys:
            task = taskqueue.Task(url = '/datastore', params = {'registry': registry})
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
        oldhash = get_cache('%s_HASH' % registry)

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
            countries = set() # 国名リスト 
            iplist = []
            for line in contents:
                record = self.record_rule.search(line)
                if record:
                    ipobj = IP(record.group(2), record.group(3), record.group(4), record.group(5), record.group(6))
                    ip = IPTable(registry = registry, cc = record.group(1), ip = ipobj)
                    iplist.append(ip)
                    countries.add(record.group(1))

            if len(iplist) == 0:
                return False
            iplist.sort(lambda x, y: cmp(x.cc, y.cc)) # 国ごとにソート

            # 一定数ごとにキャッシュに保存
            split_count = (1000)
            list_count = len(iplist) / split_count
            if list_count > 1:
                for i in xrange(list_count):
                    if not set_cache('%s_%d' % (registry, i), iplist[i * split_count : (i + 1) * split_count]):
                        return False

                # 残った分をキャッシュに保存
                if not set_cache('%s_%d' % (registry, list_count), iplist[list_count * split_count:]):
                    return False
            else:
                # 全てキャッシュに追加
                set_cache('%s_%d' % (registry, 0), iplist)

            # 国名リストをキャッシュに保存
            ctablelist = []
            for country in countries:
                ctable = Countries(cc = country, registry = registry)
                ctablelist.append(ctable)
            set_cache('%s_COUNTRIES' % registry, ctablelist)

            # ハッシュ更新
            set_cache('%s_HASH' % registry, newhash)

            logging.info('Update complete the "%s".' % registry)

class CronHandler(webapp.RequestHandler):
    def get(self):
        list = IPList()
        list.retrieve(RIR.keys())

class ViewHandler(webapp.RequestHandler):
    def get(self):
        for registry in RIR.keys():
            count = 0
            line = 0
            self.response.out.write('<strong>%s | %s</strong><br />' % (registry, get_cache('%s_HASH' % registry)))
            while True:
                cache = get_cache('%s_%d' % (registry, count))
                if not cache:
                    break

                for ipobj in cache:
                    self.response.out.write('%d:\t%s\t%d\t%s<br />' % (line, ipobj.ip.StartIP(), ipobj.ip.value, ipobj.cc))
                    line += 1
                count += 1
            self.response.out.write('<br />')

class MainHandler(webapp.RequestHandler):
    def get(self):
        countries = []
        for registry in RIR.keys():
            try:
                countries += get_cache('%s_COUNTRIES' % registry)
            except TypeError:
                logging.error('Get %s_COUNTIRES Error.' % registry)
        countries.sort(lambda x, y: cmp(x.cc, y.cc))

        template_values = {
                'title': program_title,
                'version': program_version,
                'countries': countries
                }
        path = os.path.join(os.path.dirname(__file__), 'main.html')
        self.response.out.write(template.render(path, template_values))

def main():
    application = webapp.WSGIApplication([
        ('/', MainHandler),
        ('/cron', CronHandler),
        ('/view', ViewHandler),
        ('/datastore', DataStore)],
        debug = True)
    util.run_wsgi_app(application)

### Main ###
if __name__ == '__main__':
    main()
