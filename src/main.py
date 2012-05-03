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

def GetCountries(countries):
    iptable = []
    query = common.IPStore.gql("WHERE name IN :1", countries)
    for record in query:
        storecache = pickle.loads(record.cache) if record.usepickle else record.cache
        cjson = simplejson.loads(storecache)
        for ipobj in cjson:
            ip = ips.IPDecoder(ipobj)
            iptable.append(ip)

    iptable.sort(key = lambda x : x.start)

    return iptable if len(iptable) != 0 else None

class MainHandler(webapp.RequestHandler):
    def get(self):
        try:
            countries_split = []
            iptable =[]
            
            registry = self.request.get_all('registry')
            if registry:
                # 入力された取得先の一覧を取得
                query = common.IPStore.gql("WHERE registry IN :1", registry)
                for instance in query:
                    for record in query:
                        storecache = pickle.loads(record.cache) if record.usepickle else record.cache
                        cjson = simplejson.loads(storecache)
                        for ipobj in cjson:
                            ip = ips.IPDecoder(ipobj)
                            iptable.append(ip)
            else:
                # 入力値の国名から割当IP一覧を取得
                countries = self.request.get_all('country')
                iptable = GetCountries(countries)
           
                # 全てのレジストリの国名データを取得
                logging.info('Get All Country Data')

                all_countries_cache = []
                query = common.IPStore.gql("WHERE name = :1", common.COUNTRIES_KEYNAME)
                for instance in query:
                    cclist = pickle.loads(instance.cache) \
                                        if instance.usepickle else instance.cache
                    all_countries_cache += cclist
                all_countries_cache = list(set(all_countries_cache))
                all_countries_cache.sort()

                # 国名の一文字目を基準として分割
                if all_countries_cache:
                    first = 0
                    for i in xrange(1, len(all_countries_cache)):
                        if all_countries_cache[first][0] != all_countries_cache[i][0]:
                            countries_split.append(all_countries_cache[first:i])
                            first = i
                    countries_split.append(all_countries_cache[first:])
        except TypeError:
            pass
        
        exist_rir = []
        for reg in common.RIR.keys():
            rir = common.IPStore.gql(
                    "WHERE name = :1 AND registry = :2", common.HASH_KEYNAME, reg)
            rirhash = rir.get()
            if rirhash:
                exist_rir.append(reg)
        
        template_values = { 'rir' : exist_rir,
                            'countries' : countries_split,
                            'list' : iptable
                            }
        path = os.path.join(os.path.dirname(__file__), 'index.html')
        self.response.out.write(template.render(path, template_values))

def main():
    application = webapp.WSGIApplication([
        ('/', MainHandler),
        ('/cron', CronHandler), 
        ('/datastore', datastore.DataStoreHandler), 
        ], debug=True)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
