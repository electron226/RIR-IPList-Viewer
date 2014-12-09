#!/usr/bin/env python
# -*- coding: utf-8 -*-

##
# @file iplist.py
# @brief 割当リストの取得
# @author electron226

import logging
import math
import zlib
import exceptions

from google.appengine.api import taskqueue
from google.appengine.api import urlfetch
from google.appengine.api import memcache

import common

##
# @brief IP一覧をダウンロードするクラス
class IPList():
    ##
    # @brief 結果を取得してデータをzlibに圧縮してmemcacheに保存
    #
    # @param rpc RPCオブジェクト
    # @param registry 取得した更新先のレジストリ名
    #
    # @return なし
    # @throw Exception 取得したデータを格納した辞書型をmemcacheに保存できない
    def handle_urlfetch(self, rpc, registry):
        logging.info('Download Start "%s".' % registry)

        try:
            result = rpc.get_result()
            if result.status_code != 200:
                raise urlfetch.DownloadError
        except urlfetch.DownloadError:
            logging.error('Can\'t download the file.')
            return

        try:
            cache_data = zlib.compress(result.content)
        except zlib.error:
            logging.error('Get failure. zlib Compress Error.')
            return

        segment_size = (1000000.0) # bytes(maximum length of memcache in gae)
        segment_length = int(math.ceil(float(len(cache_data)) / segment_size))

        writeDicts = {}
        try:
            for i in range(0, segment_length):
                writeDicts[str(i)] = \
                        cache_data[int(i * segment_size) : \
                                   int((i + 1) * segment_size)]

            if memcache.set_multi(writeDicts, 300,
                    common.MEMCACHE_CONTENT_KEY_PREFIX % registry):
                raise RuntimeError('Set memcache failure. "%s"' % registry)
            if not memcache.set(
                    common.MEMCACHE_CONTENT_LENGTH % registry,
                    segment_length, 300):
                raise RuntimeError(
                    'Set segment length of memcache failure. "%s"' % registry)
        except ValueError, e:
            logging.error(e)

    def create_callback(self, rpc, registry):
        return lambda: self.handle_urlfetch(rpc, registry)

    ##
    # @brief 与えたURLのIP割当ファイルの更新を確認し、取得してデータベースに登録
    #
    # @param registries 更新するレジストリの一覧の辞書型
    #
    # @return 成功したらTrue, 失敗したらFalse
    def retrieve(self, registries):
        # urlfetchで非同期接続
        rpcs = []
        for registry, url in registries.iteritems():
            rpc = urlfetch.create_rpc(deadline = 30)
            rpc.callback = self.create_callback(rpc, registry)
            urlfetch.make_fetch_call(rpc, url)
            rpcs.append(rpc)

        for rpc in rpcs:
            try:
                rpc.wait() # 完了まで待機、コールバック関数を呼び出す
            except Exception, e:
                logging.error(e)
                return False

        # タスクで取得したデータを処理
        datastore_task = taskqueue.Queue('datastore')
        tasklist = []
        for registry in registries.iterkeys():
            task = taskqueue.Task(
                    url = '/datastore',
                    params = {'registry': registry},
                    target = 'backend')
            tasklist.append(task)
        datastore_task.add(tasklist)

        return True
