#!/usr/bin/env python
# -*- coding: utf-8 -*-

##
# @file main.py
# @brief リクエストの処理
# @author khz

import os
import logging
import pickle
import datetime
import StringIO
import zipfile

# DJANGO
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from google.appengine.dist import use_library
use_library('django', '1.2')

from django.utils import simplejson

from google.appengine.api import memcache #@UndefinedVariable
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp import template

import common
import ccdict
import datastore
import ips
import iplist

##
# @brief 指定した引数のデータを取得し、json形式のリストで返す
#
# @param countries 取得する国名のリスト
# @param registry レジストリ名
#
# @return JSON形式のデータ
def GetCreateJSONList(countries, registry):
    tempdict = common.GetMultiData(countries, registry)

    jsonlist = []
    for country, ccjson in tempdict.iteritems():
        iplist_data = simplejson.loads(ccjson)
        for ipobj in iplist_data:
            ip = ips.IPDecoder(ipobj)
            json = {"country" : country, "registry": registry,
                    "StartIP": ip.StartIP(), "EndIP": ip.EndIP()}
            jsonlist.append(json)

    return jsonlist

##
# @brief 指定したレジストリのデータを取得し、json形式のリストで返す
#
# @param registries 取得するレジストリのリスト
#
# @return JSON形式のデータ
def GetRegistries(registries):
    jsonlist = []
    for registry in registries:
        ccdict = common.GetMultiData([common.COUNTRIES_KEYNAME], registry)
        for countries in ccdict.itervalues():
            jsonlist += GetCreateJSONList(countries, registry)

    return jsonlist

##
# @brief 指定した国名のデータを取得し、json形式のリストで返す
#
# @param cclist 取得する国名のリスト
#
# @return JSON形式のデータ
def GetCountries(cclist):
    jsonlist = []
    for registry in common.RIR:
        ccdict = common.GetMultiData([common.COUNTRIES_KEYNAME], registry)

        getlist = []
        for countries in ccdict.itervalues():
            ccset = set(countries)
            argset = set(cclist)
            getlist += ccset.intersection(argset)

        jsonlist += GetCreateJSONList(getlist, registry)

    return jsonlist

##
# @brief JSONのリクエスト処理を行うクラスのベースクラス
class GetJSONBase(webapp.RequestHandler):
    ##
    # @brief リクエストとともに渡された引数を受け取り、それを元にJSONを取得。
    #
    # @return JSON形式のデータ
    def GetJSONSwitch(self):
        registry = self.request.get('registry')
        if registry:
            registries = registry.split(',')
            jsonlist = GetRegistries(registries)
        else:
            country = self.request.get('country')
            if country:
                countries = country.split(',')
                jsonlist = GetCountries(countries)
            else:
                # 空
                jsonlist = [{"country" : "", "registry": "", "StartIP": "", "EndIP": ""}]

        jsonlist.sort(lambda x, y: cmp(x["country"], y["country"]));
        jsonlist.sort(lambda x, y: cmp(x["registry"], y["registry"]));

        return jsonlist

##
# @brief AjaxでJSONデータを取得するのに使うクラス
class GetJSONHandler(GetJSONBase):
    ##
    # @brief GETリクエストを受け取り、json形式のデータを出力する
    #
    # @return なし
    def get(self):
        jsonlist = self.GetJSONSwitch()

        ccjson = simplejson.dumps(jsonlist)

        self.response.content_type = "application/json"
        self.response.out.write(ccjson)

##
# @brief サーバ側でJSONデータの加工処理を行うクラス
class GetJSONCustomHandler(GetJSONBase):
    ##
    # @brief GETリクエストを受け取り、指定した形式でJSONデータを出力
    #
    # @return なし
    def get(self):
        jsonlist = self.GetJSONSwitch()

        settings = self.request.get('settings')
        if settings:
            liststr = ""
            for json in jsonlist:
                tempstr = settings.replace(r'<REGISTRY>', json["registry"])
                tempstr = tempstr.replace(r'<CC>', json["country"])
                tempstr = tempstr.replace(r'<IPSTART>', json["StartIP"])
                liststr += tempstr.replace(r'<IPEND>', json["EndIP"])
                #liststr += "<br>"
                liststr += "\n"
            """
            self.response.content_type = "text/plain"
            self.response.out.write(liststr)
            """
            
            # ZIP作成
            zipdata = StringIO.StringIO()
            zipobj = zipfile.ZipFile(zipdata, 'w', zipfile.ZIP_DEFLATED)
            zipobj.writestr('list.txt', liststr.encode("utf-8"))
            zipobj.close()
            zipdata.seek(0)

            # データを返す
            self.response.headers['Content-Type'] ='application/zip'
            self.response.headers['Content-Disposition'] = \
                    'attachment; filename=list.zip'	
            self.response.out.write(zipdata.getvalue())

##
# @brief 定期的にスケジュール処理をするクラス
class CronHandler(webapp.RequestHandler):
    ##
    # @brief リクエストを受け取ったら更新処理
    #
    # @return なし
    def get(self):
        ipl = iplist.IPList()
        ipl.retrieve(common.RIR)

##
# @brief トップページのリクエストを処理するクラス
class MainHandler(webapp.RequestHandler):
    ##
    # @brief サイトのTOPページのリクエストを処理
    #
    # @return なし
    def get(self):
        # 全てのレジストリの国名データを取得
        all_countries_cache = []
        for registry in common.RIR.iterkeys():
            try:
                recordlist = common.GetMultiData(
                        [common.COUNTRIES_KEYNAME], registry)
            except RuntimeError, re:
                logging.warning(re)
                continue
            all_countries_cache += recordlist[common.COUNTRIES_KEYNAME]
        all_countries_cache = list(set(all_countries_cache))

        # 国名の文字コードと国名を辞書型で設定
        ccdict_name = ccdict.countries_dict
        all_countries_dict = {}
        for country in all_countries_cache:
            if ccdict_name.has_key(country):
                all_countries_dict[country] = ccdict_name[country]
            else:
                all_countries_dict[country] = ''

        # 取得済みのレジストリの取得
        exist_rir = {}
        rirrecords = common.IPStore.gql("WHERE name = :1", common.HASH_KEYNAME)
        for record in rirrecords:
            registry = record.registry
            exist_rir[registry] = common.RIREXP[registry]

        # 最後の更新日時のデータを取得
        lastupdate = memcache.get(common.MEMCACHE_LASTUPDATE) #@UndefinedVariable
        if not lastupdate:
            timerecord = common.GetLastUpdateDate()
            if timerecord:
                uptime = timerecord.time
                uptime += datetime.timedelta(hours = 9)
                lastupdate = uptime.strftime("%Y/%m/%d %H:%M:%S")
                if not memcache.set(common.MEMCACHE_LASTUPDATE, lastupdate): #@UndefinedVariable
                    logging.error("Can't set memcache of last update time.")

        template_values = { 'rir' : sorted(exist_rir.items(),
                                            lambda x, y: cmp(x, y)),
                            'countries' : sorted(all_countries_dict.items(),
                                lambda x, y: cmp(x, y)),
                            'lastupdate' : lastupdate,
                            }
        path = os.path.join(os.path.dirname(__file__), 'index.html')
        self.response.out.write(template.render(path, template_values))

##
# @brief webappを使った処理の開始
#
# @return なし
def main():
    application = webapp.WSGIApplication([
        ('/', MainHandler),
        ('/json', GetJSONHandler),
        ('/jsoncustom', GetJSONCustomHandler),
        ('/cron', CronHandler),
        ('/datastore', datastore.DataStoreHandler),
        ], debug=False)
    util.run_wsgi_app(application)

##
# @brief スタート位置
if __name__ == '__main__':
    main()
