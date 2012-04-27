#!/usr/bin/env python
# vim: set fileencoding=utf-8
import re
import hashlib
import zlib
import logging

from django.utils import simplejson
from google.appengine.ext import webapp
from google.appengine.api import memcache

import common
import ips

# ハッシュ値確認用
header_rule = re.compile(r'\d{1}\|[a-z]+\|\d+\|\d+\|\d+\|\d+\|[+-]?\d+')

# レコード用(IPv4)
# xxx.xxx.xxx.xxx
#  G2  G3  G4  G5
# G1 = 国コード, G6 = 範囲
record_rule = re.compile(r'([A-Z]{2})\|ipv4\|(\d+).(\d+).(\d+).(\d+)\|(\d+)')

class DataStoreHandler(webapp.RequestHandler):
    # 最適化
    # cciplist : 国名別に分けられたIP一覧のdict
    def Combine(self, cciplist):
        for values in cciplist.itervalues():
            SaveAddress = None
            for i in xrange(len(values) - 1):
                IPList = values

                # 現在のIP範囲の末尾と次のIP範囲の開始が同じ
                if IPList[i].end == IPList[i + 1].start:
                    if not SaveAddress:
                        # まだ統合されていないIP範囲
                        SaveAddress = i
                        IPList[i].end = IPList[i + 1].end
                        IPList[i + 1].start = None
                        IPList[i].value += IPList[i + 1].value
                    else:
                        # 以前に統合したことがあるIP範囲
                        IPList[SaveAddress].end = IPList[i + 1].end
                        IPList[i + 1].start = None
                        IPList[SaveAddress].value += IPList[i + 1].value
                else:
                    SaveAddress = None

        # 不要部分削除
        for values in cciplist.itervalues():
            clear_list = [x for x in values if x.start == None]
            for clear in clear_list:
                values.remove(clear)

    def post(self):
        global reghash_keyname
        global header_rule
        global record_rule

        registry = self.request.get('registry')

        try:
            cache = memcache.get(registry) #@UndefinedVariable
            data = cache['data']
            crc = cache['crc']
            content = zlib.decompress(data)
            if common.CRC32Check(content) != crc:
                logging.error('memcache "%s" be dameged.' % registry)
                return False
        except TypeError, te:
            logging.error(te)
            return False
        except zlib.error:
            logging.error('zlib Decompress Error. "%s"' % registry)
            return False

        # 取得したIP一覧を改行コードで分割
        try:
            contents = content.split('\n')
        except UnboundLocalError, ule:
            logging.error('%s' % ule)
            return False

        # 前回のハッシュ値を取得
        oldhash = common.get_cache(common.reghash_keyname % registry)

        # 前回のハッシュ値と今回のハッシュ値を比較
        newget = True
        newhash = None
        for line in contents:
            header = header_rule.match(line)
            if header:
                newhash = hashlib.md5(header.group()).hexdigest()
                if oldhash != None and oldhash == newhash:
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
            common.Clear(registry)

            # 取得したIP一覧を最適化後に保存
            iplist = {}
            for line in contents:
                record = record_rule.search(line)
                if record:
                    ipobj = ips.IP(record.group(2), record.group(3),
                            record.group(4), record.group(5), record.group(6))
                    try:
                        iplist[record.group(1)].append(ipobj)
                    except KeyError:
                        iplist[record.group(1)] = []
                        iplist[record.group(1)].append(ipobj)

            if len(iplist) == 0:
                return False

            # 最適化
            self.Combine(iplist)

            # 保存
            for country, value in iplist.items():
                # 既に別のレジストリから追記されているデータに追記させる
                olddata = common.get_cache(country)
                if olddata:
                    cjson = simplejson.loads(olddata)
                    oldip = []
                    for ipobj in cjson:
                        ip = ips.IPDecoder(ipobj)
                        oldip.append(ip)
                    value = oldip + value
                    
                # 保存
                ccjson = simplejson.dumps(value, cls = ips.IPEncoder)
                if not common.set_cache('%s' % country, ccjson, True):
                    logging.error('iplist cache failure. "%s"' % country)
                    return False

            # 国名一覧をキャッシュに保存
            common.set_cache(common.countries_keyname % registry, iplist.keys(), True)

            # Update Hash
            common.set_cache(common.reghash_keyname % registry, newhash, False)

            logging.info('Update complete the "%s".' % registry)