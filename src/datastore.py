#!/usr/bin/env python
# vim: set fileencoding=utf-8
import re
import hashlib
import zlib
import logging

from django.utils import simplejson
from google.appengine.api import memcache
from google.appengine.ext import webapp

import common
import ips

# IP一覧を保存する
# memcacheの最大保存期間(秒)
# 最高期間: 1ヶ月
memcache_time = (129600)

# ハッシュ値確認用
header_rule = re.compile(r'\d{1}\|[a-z]+\|\d+\|\d+\|\d+\|\d+\|[+-]?\d+')

# レコード用(IPv4)
# xxx.xxx.xxx.xxx
#  G2  G3  G4  G5
# G1 = 国コード, G6 = 範囲
record_rule = re.compile(r'([A-Z]{2})\|ipv4\|(\d+).(\d+).(\d+).(\d+)\|(\d+)')

class DataStoreHandler(webapp.RequestHandler):
    # 最適化
    # ccipdict : 国名別に分けられたIP一覧のdict
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
        
    def post(self):
        registry = self.request.get('registry')

        try:
            cache = memcache.get(common.MEMCACHE_CONTENT % registry) #@UndefinedVariable
            data = cache['data']
            crc = cache['crc']
        except TypeError, te:
            logging.error(te)
            return False

        try:
            content = zlib.decompress(data)
            if common.CRC32Check(content) != crc:
                logging.error('memcache "%s" be dameged.' % registry)
                return False
        except zlib.error:
            logging.error('zlib Decompress Error. "%s"' % registry)
            return False

        # 取得したIP一覧を改行コードで分割
        contents = content.split('\n')

        # 前回のハッシュ値を取得
        hashlist = common.ReadRecord(common.HASH_KEYNAME, registry)
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
            common.ClearRecord(registry);
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

            # Update Hash
            common.WriteRecord(common.HASH_KEYNAME, registry, newhash, False)

            # 更新日時更新
            common.WriteDate(registry)

            # memcache Update
            memcache.set_multi(memcache_dict, memcache_time, registry) #@UndefinedVariable

            logging.info('Get Update IPList End. "%s"' % registry)
            logging.info('Update complete the "%s".' % registry)
