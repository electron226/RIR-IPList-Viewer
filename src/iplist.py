#!/usr/bin/env python
# vim: set fileencoding=utf-8

import logging
import zlib

from google.appengine.api import taskqueue
from google.appengine.api import urlfetch
from google.appengine.api import memcache

import common

# IP一覧をダウンロードするクラス
class IPList():
    # 取得したデータをzlibに圧縮してmemcacheに保存
    def handle_urlfetch(self, rpc, registry):
        logging.info('Download Start "%s".' % registry)
        try:
            result = rpc.get_result()
            if result.status_code != 200:
                logging.error('Failed to open "%s".' % registry)
                return False
            
            cache_data = {
                          'data': zlib.compress(result.content),
                          'crc': common.CRC32Check(result.content) }
            if not memcache.set(
                    common.REGISTRY_CONTENT % registry, cache_data, 300): #@UndefinedVariable
                logging.error('Set , %s content failure.' % registry)
        except urlfetch.DownloadError:
            logging.error('Get "%s" failure.' % registry)
        except zlib.error:
            logging.error('Get "%s" failure. zlib Compress Error.' % registry)

    def create_callback(self, rpc, registry):
        return lambda: self.handle_urlfetch(rpc, registry)

    # 与えたURLのIP割当ファイルの更新を確認し、取得してデータベースに登録
    # registries : 更新するregistryの一覧のdict型
    def retrieve(self, registries):
        # urlfetchで非同期接続
        rpcs = []
        for registry, url in registries.iteritems():
            rpc = urlfetch.create_rpc(deadline = 30)
            rpc.callback = self.create_callback(rpc, registry)
            urlfetch.make_fetch_call(rpc, url)
            rpcs.append(rpc)

        for rpc in rpcs:
            rpc.wait() # 完了まで待機、コールバック関数を呼び出す

        # タスクで取得したデータを処理
        datastore_task = taskqueue.Queue('datastore')
        tasklist = []
        for registry in registries.iterkeys():
            task = taskqueue.Task(
                    url = '/datastore', 
                    params = {'registry': registry})
            tasklist.append(task)
        datastore_task.add(tasklist)
