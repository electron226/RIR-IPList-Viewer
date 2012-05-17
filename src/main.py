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
import types

# DJANGO
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from google.appengine.dist import use_library
use_library('django', '1.2')

from django.utils import simplejson

from google.appengine.api import memcache
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp import template

import common
import ips
import iplist
import datastore

def GetCreateJSONListFromCache(countries, registry):
    tempdict = memcache.get_multi(countries, registry)
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
        ccdict = memcache.get_multi([common.COUNTRIES_KEYNAME], registry)

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
        ccdict = memcache.get_multi([common.COUNTRIES_KEYNAME], registry)

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

def GetJSONSwitch(handler):
    registry = handler.request.get('registry')
    if registry:
        registries = registry.split(',')
        jsonlist = GetRegistriesCache(registries)
        if len(jsonlist) == 0:
            jsonlist = GetRegistriesRecords(registries)
    else:
        country = handler.request.get('country')
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
        all_countries_cache.sort()

        exist_rir = []
        for reg in common.RIR.keys():
            rir = common.IPStore.gql(
                    "WHERE name = :1 AND registry = :2", common.HASH_KEYNAME, reg)
            rirhash = rir.get()
            if rirhash:
                exist_rir.append(reg)
        exist_rir.sort()
        
        template_values = { 'rir' : exist_rir,
                            'countries' : all_countries_cache,
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
