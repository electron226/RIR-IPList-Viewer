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

class ViewHandler(webapp.RequestHandler):
    def get(self):
        for registry in common.RIR.keys():
            reghash = common.ReadRecord(common.reghash_keyname % registry)
            self.response.out.write(
                    '<strong>%s | %s</strong><br />' % (registry, reghash))

            line = 0
            countries_cache = common.ReadRecord(
                    common.countries_keyname % registry)
            if countries_cache == None:
                continue

            for country in countries_cache:
                cache = common.ReadRecord('%s' % country)
                if cache == None:
                    continue
                ccjson = simplejson.loads(cache)

                for ipobj in ccjson:
                    ip = ips.IPDecoder(ipobj)
                    self.response.out.write('%d:\t%s\t%d\t%s<br />'
                            % (line, ip.StartIP(), ip.value, country))
                    line += 1
            self.response.out.write('<br />')

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
            # 入力された取得先の一覧を取得
            registry = self.request.get_all('registry')
            
            # 入力値の国名から割当IP一覧を取得
            countries = self.request.get_all('country')
            iptable = GetCountries(countries)
            logging.info(iptable)
       
            # キャッシュをした分割の国名データを取得
            logging.info('Get All Country Data')
            all_countries_cache = common.ReadRecord(common.countries_keyname % "ALL")
            countries_split = all_countries_cache if all_countries_cache else []
            if not countries_split:
                # 取得している全ての国名を取得
                countries_list = []
                for registry in common.RIR.keys():
                    countries_list += common.ReadRecord(common.countries_keyname % registry)
                countries_list = list(set(countries_list))
                countries_list.sort()
                
                # 国名の一文字目を基準として分割
                first = 0
                if countries_list:
                    for i in xrange(1, len(countries_list)):
                        if countries_list[first][0] != countries_list[i][0]:
                            countries_split.append(countries_list[first:i])
                            first = i
                countries_split.append(countries_list[first:])
                
                # 分割した国名リストをキャッシュ
                if common.WriteRecord(common.countries_keyname % "ALL", countries_split, True):
                    logging.info("ALL Countries Cache Update.")
                else:
                    logging.error('ALL Countries Save failure.')
        except TypeError:
            pass
        
        exist_rir = []
        for rir in common.RIR.keys():
            rir_cache = common.ReadRecord(common.reghash_keyname % rir)
            if rir_cache:
                exist_rir.append(rir)
        
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
        ('/view', ViewHandler), 
        ('/datastore', datastore.DataStoreHandler), 
        ], debug=True)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
