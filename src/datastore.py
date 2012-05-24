#!/usr/bin/env python
# vim: set fileencoding=utf-8

##
# @file datastore.py
# @brief IP割当一覧のデータストア書き込み
# @author khz

import re
import hashlib
import zlib
import logging

from django.utils import simplejson
from google.appengine.api import memcache
from google.appengine.ext import webapp

import common
import ips

## 正規表現(ハッシュ値確認用)
header_rule = re.compile(r'\d{1}\|[a-z]+\|\d+\|\d+\|\d+\|\d+\|[+-]?\d+')

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
class DataStoreHandler(webapp.RequestHandler):
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
    # @return 更新が成功したか否か(True, False)
    def post(self):
        registry = self.request.get('registry')

        cache = memcache.get(common.MEMCACHE_CONTENT % registry) #@UndefinedVariable
        if not cache:
            return False

        try:
            content = zlib.decompress(cache)
        except zlib.error:
            logging.error('zlib Decompress Error. "%s"' % registry)
            return False

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
            logging.error('Search the "%s" header.' % registry)
            return False

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
                return False

            # 最適化
            logging.info('IPList Combine Start.')
            self.Combine(ipdict)
            logging.info('IPList Combine End.')
       
            # 保存
            logging.info('Get Update IPList Start. "%s"' % registry)

            # memcacheとデータストアに保存
            memcache_dict = {}
            for country, value in ipdict.iteritems():
                ccjson = simplejson.dumps(value, cls = ips.IPEncoder)
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
