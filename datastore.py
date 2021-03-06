﻿#!/usr/bin/env python
# -*- coding: utf-8 -*-

##
# @file datastore.py
# @brief IP割当一覧のデータストア書き込み
# @author electron226

import re
import hashlib
import zlib
import logging
import json

import webapp2
from google.appengine.api import memcache

import common
import ips

## 正規表現(ハッシュ値確認用)
header_rule = re.compile(r'[\d.]+\|[a-z]+\|\d*\|\d*\|\d*\|\d*\|[+-]?\d+')

##
# @brief 正規表現(レコード用, IPv4)\n
#        xxx.xxx.xxx.xxx\n
#        G2  G3  G4  G5\n
#        G1 = 国コード, G6 = 範囲
record_rule = re.compile(r'([A-Z]{2})\|ipv4\|(\d+).(\d+).(\d+).(\d+)\|(\d+)')

##
# @brief リクエストを受け取り、更新処理を行う。
#
#        更新に使うデータはIPListクラスで保存されている。
class DataStoreHandler(webapp2.RequestHandler):
    ##
    # @brief 割当一覧の最適化(圧縮)処理。
    #
    # @param ccipdict 国名別に分けられたIP一覧の辞書型。中身を操作される。
    #
    # @return なし
    def Combine(self, ccipdict):
        for values in ccipdict.itervalues():
            if len(values) < 2:
                continue
            
            #################################################################
            # マルチスレッド化予定
            #################################################################
            i = 0
            j = i + 1
            while j < len(values):
                IPList = values

                # 現在のIP範囲の末尾と次のIP範囲の開始が同じ
                if IPList[i].end == IPList[j].start:
                    IPList[i].end = IPList[j].end
                    IPList[j].start = None
                    IPList[i].value += IPList[j].value
                    
                    j += 1
                else:
                    del values[i + 1:j]
                    i += 1
                    j = i + 1
            # 残った分も削除
            # i + 1 == jの場合、
            # 処理が行われず、参照する値が範囲外でも例外が発生しない
            del values[i + 1:j]
        
    ##
    # @brief リクエストを受け取り、更新処理を行う
    #
    #        更新に使うデータはIPListクラスで保存されている。
    #
    # @return なし
    def post(self):
        registry = self.request.get('registry')

        segment_length = memcache.get(common.MEMCACHE_CONTENT_LENGTH % registry)
        if segment_length is None:
            logging.error(
                "Don't update registry." +
                " Can't get the content of the registry. '%s'" % registry)
            return

        getKeys = []
        for i in xrange(0, segment_length):
            getKeys.append(str(i))
        contents = memcache.get_multi(
                getKeys, common.MEMCACHE_CONTENT_KEY_PREFIX % registry)

        cache = ''
        for i in xrange(0, segment_length):
            cache = cache + contents[str(i)]

        memcache.delete(common.MEMCACHE_CONTENT_LENGTH % registry)
        memcache.delete_multi(
                keys = getKeys,
                key_prefix = common.MEMCACHE_CONTENT_KEY_PREFIX % registry)

        try:
            content = zlib.decompress(cache)
        except zlib.error:
            logging.error('zlib Decompress Error. "%s"' % registry)
            return

        # 取得したIP一覧を改行コードで分割
        contents = content.split('\n')

        # 前回のハッシュ値を取得
        hashlist = common.ReadRecord(name = common.HASH_KEYNAME, registry = registry)
        oldhash = hashlist[0] if len(hashlist) > 0 else None

        # 前回のハッシュ値と今回のハッシュ値を比較
        newget = True
        newhash = None
        for line in contents:
            header = header_rule.match(line)
            if header:
                newhash = hashlib.md5(header.group()).hexdigest()
                if oldhash is not None and oldhash == newhash:
                    # 前回と同一のハッシュの場合
                    newget = False
                    logging.info('Already Latest Edition the "%s".' % registry)
                break

        if not newhash:
            logging.error('do not find the "%s" header.' % registry)
            return

        if newget:
            logging.info('Start update the "%s".' % registry)

            # 一致するレジストリのキャッシュを削除
            logging.debug('Old IPList Clear Start. "%s".' % registry)
            common.DeleteRecord(registry = registry);
            logging.debug('Old IPList Clear Start "%s".' % registry)

            # 取得したIP一覧を最適化後に保存
            ipdict = {}
            for line in contents:
                record = record_rule.search(line)
                if record:
                    ipobj = ips.IP(record.group(2), record.group(3),
                            record.group(4), record.group(5), record.group(6))
                    if not ipdict.has_key(record.group(1)):
                        ipdict[record.group(1)] = []
                    ipdict[record.group(1)].append(ipobj)

            if len(ipdict) == 0:
                return

            # 最適化
            logging.info('IPList Combine Start.')
            self.Combine(ipdict)
            logging.info('IPList Combine End.')

            # 保存
            logging.info('Get Update IPList Start. "%s"' % registry)

            # memcacheとデータストアに保存
            memcache_dict = {}
            for country, ipobj in ipdict.iteritems():
                ccjson = json.dumps(ipobj, cls = ips.IPEncoder)
                common.WriteRecord(country, registry, ccjson, True)
                memcache_dict["%s" % country] = ccjson

            # 国名一覧をキャッシュに保存
            common.WriteRecord(common.COUNTRIES_KEYNAME, registry, ipdict.keys(), True)
            memcache_dict[common.COUNTRIES_KEYNAME] = ipdict.keys()

            # Update Hash(ハッシュだけはmemcacheを使わない)
            common.WriteRecord(common.HASH_KEYNAME, registry, newhash, False)

            # 更新日時更新
            common.WriteDate(registry)

            # memcache Update
            memcache.set_multi(memcache_dict, common.memcache_time, registry) #@UndefinedVariable

            logging.info('Get Update IPList End. "%s"' % registry)
            logging.info('Update complete the "%s".' % registry)
