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

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp import template

import common
import ips
import iplist
import datastore

class CronHandler(webapp.RequestHandler):
    def get(self):
        ipl = iplist.IPList()
        ipl.retrieve(common.RIR)

def GetRegistries(registry):
    jsonlist = []

    query = common.IPStore.gql("WHERE registry IN :1", registry)
    for record in query:
        # 国要素以外スキップ
        if len(record.name) != 2:
            continue

        storecache = pickle.loads(record.cache) if record.usepickle else record.cache
        cjson = simplejson.loads(storecache)
        for ipobj in cjson:
            ip = ips.IPDecoder(ipobj)
            json = {"country" : record.name, "registry": record.registry,
                    "StartIP": ip.StartIP(), "EndIP": ip.EndIP()}
            jsonlist.append(json)
    jsonlist.sort(lambda x, y: cmp(x["country"], y["country"]));
    jsonlist.sort(lambda x, y: cmp(x["registry"], y["registry"]));

    return jsonlist

def GetCountries(country):
    jsonlist = []

    query = common.IPStore.gql("WHERE name IN :1", country)
    for record in query:
        storecache = pickle.loads(record.cache) if record.usepickle else record.cache
        cjson = simplejson.loads(storecache)
        for ipobj in cjson:
            ip = ips.IPDecoder(ipobj)
            json = {"country" : record.name, "registry": record.registry,
                    "StartIP": ip.StartIP(), "EndIP": ip.EndIP()}
            jsonlist.append(json)
    jsonlist.sort(lambda x, y: cmp(x["country"], y["country"]));
    jsonlist.sort(lambda x, y: cmp(x["registry"], y["registry"]));

    return jsonlist

class GetJSONHandler(webapp.RequestHandler):
    def get(self):
        registry = self.request.get('registry')
        if registry:
            registries = registry.split(',')
            jsonlist = GetRegistries(registries)
        else:
            country = self.request.get('country')
            if country:
                countries = country.split(',')
                countries30 = common.Split_Seq(countries, 30)
                jsonlist = []
                for cclist in countries30:
                    jsonlist += GetCountries(cclist)
            else:
                # 空
                jsonlist = [{"country" : "", "registry": "", "StartIP": "", "EndIP": ""}]

        ccjson = simplejson.dumps(jsonlist)

        self.response.content_type = "application/json"
        self.response.out.write(ccjson)

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
        ('/cron', CronHandler), 
        ('/datastore', datastore.DataStoreHandler), 
        ], debug=True)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
