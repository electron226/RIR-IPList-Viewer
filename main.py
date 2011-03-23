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
import cgi

from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.ext.webapp import util

class Version(db.Model):
    registry = db.StringProperty()
    hash = db.ByteString()

class IPTable(db.Model):
    registry = db.StringProperty()
    cc = db.StringProperty()
    start = db.StringProperty()
    value = db.IntegerProperty()

class MainHandler(webapp.RequestHandler):
    def get(self):
        self.response.out.write('<html><body>')

        iptable = db.GqlQuery("SELECT * FROM IPTable")

        for record in iptable:
            self.response.out.write('registry: %s<br>' % cgi.escape(record.registry))

        self.response.out.write("""
        <form action="/sign" method="post">
        <div><textarea name="registry" cols="10"></textarea></div>
        <div><input type="submit" value="Submit"></div>
        </form>
        """)
        self.response.out.write('</body></html>')

class Guestbook(webapp.RequestHandler):
    def post(self):
        iptable = IPTable()

        iptable.registry = self.request.get('registry')
        iptable.put()
        self.redirect('/')

def main():
    application = webapp.WSGIApplication([('/', MainHandler), ('/sign', Guestbook)], debug=True)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
