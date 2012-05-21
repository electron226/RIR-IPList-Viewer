#!/usr/bin/env python
# vim: set fileencoding=utf-8
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import os
import logging
import pickle
import datetime

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
import ips
import iplist
import datastore
import ccdict

def GetCreateJSONListFromCache(countries, registry):
    tempdict = memcache.get_multi(countries, registry) #@UndefinedVariable
    if len(tempdict) == 0:
        logging.error("GetCreateJSONListFromCache(): memcache.get_multi(): \
                        key: %s prefix: %s" % (countries, registry))
        return []

    # 一つでも取得できなかったデータがある場合、
    # エラーとして空リストを返す
    for country in countries:
        if not tempdict.has_key(country):
            logging.error("GetCreateJSONListFromCache(): %s" % country)
            return []

    jsonlist = []
    for country, ccjson in tempdict.iteritems():
        iplist = simplejson.loads(ccjson)
        for ipobj in iplist:
            ip = ips.IPDecoder(ipobj)
            json = {"country" : country, "registry": registry,
                    "StartIP": ip.StartIP(), "EndIP": ip.EndIP()}
            jsonlist.append(json)

    return jsonlist

def GetRegistriesCache(registries):
    jsonlist = []
    for registry in registries:
        ccdict = memcache.get_multi([common.COUNTRIES_KEYNAME], registry) #@UndefinedVariable

        # 取得できなかった場合、エラーとして空リストを返す
        if not ccdict.has_key(common.COUNTRIES_KEYNAME):
            logging.error(
                    "GetRegistriesCache(): No Get memcache.: %s" % registry)
            return []

        for countries in ccdict.itervalues():
            jsonlist += GetCreateJSONListFromCache(countries, registry)

    return jsonlist

def GetCountriesCache(cclist):
    jsonlist = []
    for registry in common.RIR:
        ccdict = memcache.get_multi([common.COUNTRIES_KEYNAME], registry) #@UndefinedVariable

        # 取得できなかった場合、エラーとして空リストを返す
        if not ccdict.has_key(common.COUNTRIES_KEYNAME):
            logging.error(
                    "GetCountriesCache(): No Get memcache.: %s" % registry)
            return []

        getlist = []
        for countries in ccdict.itervalues():
            for cc in cclist:
                if cc in countries:
                    getlist.append(cc)

        jsonlist += GetCreateJSONListFromCache(getlist, registry)

    return jsonlist

def GetRegistriesRecords(registries):
    jsonlist = []
    query = common.IPStore.gql("WHERE registry IN :1", registries)
    for record in query:
        # 国名データ以外はスキップ
        if len(record.name) != 2:
            continue

        storecache = pickle.loads(record.cache) if record.usepickle else record.cache
        cjson = simplejson.loads(storecache)
        for ipobj in cjson:
            ip = ips.IPDecoder(ipobj)
            json = {"country" : record.name, "registry": record.registry,
                    "StartIP": ip.StartIP(), "EndIP": ip.EndIP()}
            jsonlist.append(json)

    return jsonlist

def GetCountriesRecords(countries):
    jsonlist = []
    query = common.IPStore.gql("WHERE name IN :1", countries)
    for record in query:
        storecache = pickle.loads(record.cache) if record.usepickle else record.cache
        cjson = simplejson.loads(storecache)
        for ipobj in cjson:
            ip = ips.IPDecoder(ipobj)
            json = {"country" : record.name, "registry": record.registry,
                    "StartIP": ip.StartIP(), "EndIP": ip.EndIP()}
            jsonlist.append(json)

    return jsonlist

def GetJSONSwitch(self):
    registry = self.request.get('registry')
    if registry:
        registries = registry.split(',')
        jsonlist = GetRegistriesCache(registries)
        if len(jsonlist) == 0:
            jsonlist = GetRegistriesRecords(registries)
    else:
        country = self.request.get('country')
        if country:
            countries = country.split(',')
            jsonlist = GetCountriesCache(countries)
            if len(jsonlist) == 0:
                jsonlist = []
                countries30 = common.Split_Seq(countries, 30)
                for cclist in countries30:
                    jsonlist += GetCountriesRecords(cclist)
        else:
            # 空
            jsonlist = [{"country" : "", "registry": "", "StartIP": "", "EndIP": ""}]

    jsonlist.sort(lambda x, y: cmp(x["country"], y["country"]));
    jsonlist.sort(lambda x, y: cmp(x["registry"], y["registry"]));

    return jsonlist

class GetJSONHandler(webapp.RequestHandler):
    def get(self):
        jsonlist = GetJSONSwitch(self)

        ccjson = simplejson.dumps(jsonlist)

        self.response.content_type = "application/json"
        self.response.out.write(ccjson)

class GetJSONCustomHandler(webapp.RequestHandler):
    def get(self):
        jsonlist = GetJSONSwitch(self)

        settings = self.request.get('settings')
        if settings:
            liststr = ""
            for json in jsonlist:
                tempstr = settings.replace(r'<REGISTRY>', json["registry"])
                tempstr = tempstr.replace(r'<CC>', json["country"])
                tempstr = tempstr.replace(r'<IPSTART>', json["StartIP"])
                liststr += tempstr.replace(r'<IPEND>', json["EndIP"])
                liststr += "<br>"
            self.response.content_type = "text/plain"
            self.response.out.write(liststr)

class CronHandler(webapp.RequestHandler):
    def get(self):
        ipl = iplist.IPList()
        ipl.retrieve(common.RIR)

class MainHandler(webapp.RequestHandler):
    def get(self):
        # 全てのレジストリの国名データを取得
        all_countries_cache = []
        query = common.IPStore.gql("WHERE name = :1", common.COUNTRIES_KEYNAME)
        for instance in query:
            cclist = pickle.loads(instance.cache) \
                                if instance.usepickle else instance.cache
            all_countries_cache += cclist
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
        for reg in common.RIR.keys():
            rir = common.IPStore.gql(
                    "WHERE name = :1 AND registry = :2", common.HASH_KEYNAME, reg)
            rirhash = rir.get()
            if rirhash:
                exist_rir[reg] = common.RIREXP[reg]

        # 最後の更新日時のデータを取得
        lastupdate = memcache.get(common.MEMCACHE_LASTUPDATE)
        if not lastupdate:
            timerecord = common.GetLastUpdateDate()
            if timerecord:
                uptime = timerecord.time
                uptime += datetime.timedelta(hours = 9)
                lastupdate = uptime.strftime("%Y/%m/%d %H:%M:%S")
                if not memcache.set(common.MEMCACHE_LASTUPDATE, lastupdate):
                    logging.error("Can't set memcache of last update time.")
        
        template_values = { 'rir' : sorted(exist_rir.items(),
                                            lambda x, y: cmp(x, y)),
                            'countries' : sorted(all_countries_dict.items(),
                                lambda x, y: cmp(x, y)),
                            'lastupdate' : lastupdate,
                            }
        path = os.path.join(os.path.dirname(__file__), 'index.html')
        self.response.out.write(template.render(path, template_values))

def main():
    application = webapp.WSGIApplication([
        ('/', MainHandler),
        ('/json', GetJSONHandler),
        ('/jsoncustom', GetJSONCustomHandler),
        ('/cron', CronHandler), 
        ('/datastore', datastore.DataStoreHandler), 
        ], debug=True)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
