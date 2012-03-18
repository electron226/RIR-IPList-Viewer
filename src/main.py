#!/usr/bin/env python
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
from django.utils import simplejson
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util

import common
import ips
import iplist
import datastore

class CronHandler(webapp.RequestHandler):
    def get(self):
        ips = iplist.IPList()
        ips.retrieve(common.RIR)

class ViewHandler(webapp.RequestHandler):
    def get(self):
        for registry in common.RIR.keys():
            reghash = common.get_cache(common.reghash_keyname % registry)
            self.response.out.write(
                    '<strong>%s | %s</strong><br />' % (registry, reghash))

            line = 0
            countries_cache = common.get_cache(
                    common.countries_keyname % registry)
            if countries_cache == None:
                continue

            for country in countries_cache:
                cache = common.get_cache('%s' % country)
                if cache == None:
                    continue
                ccjson = simplejson.loads(cache)

                for ipobj in ccjson:
                    ip = ips.IPDecoder(ipobj)
                    self.response.out.write('%d:\t%s\t%d\t%s<br />'
                            % (line, ip.StartIP(), ip.value, country))
                    line += 1
            self.response.out.write('<br />')

class MainHandler(webapp.RequestHandler):
    def get(self):
        self.response.out.write('Hello world!')

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
