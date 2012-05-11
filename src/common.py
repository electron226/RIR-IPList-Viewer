#!/usr/bin/env python
# vim: set fileencoding=utf-8
import pickle
import logging
import zlib

from google.appengine.api import memcache
from google.appengine.ext import db

# ----------------------------------------------------------------------------
# 取得先
RIR = {
#        'ICANN':'http://ftp.apnic.net/stats/iana/delegated-iana-latest',
#        'ARIN':'http://ftp.apnic.net/stats/arin/delegated-arin-latest',
#        'APNIC':'http://ftp.apnic.net/stats/apnic/delegated-apnic-latest',
#        'RIPE':'http://ftp.apnic.net/stats/ripe-ncc/delegated-ripencc-latest',
#        'LACNIC':'http://ftp.apnic.net/stats/lacnic/delegated-lacnic-latest',
        'AFRINIC':'http://ftp.apnic.net/stats/afrinic/delegated-afrinic-latest'
        }

# データベースに保存されるデータのキー名
# "%s"部分は文字列に置き換えられる
REGISTRY_CONTENT = '%s_CONTENT' # 取得したデータの一時保存用(memcache用)

HASH_KEYNAME = 'HASH'
COUNTRIES_KEYNAME = 'COUNTRIES'

# ----------------------------------------------------------------------------

def CRC32Check(string):
    return zlib.crc32(string) & 0xFFFFFFFF

# ----------------------------------------------------------------------------

class IPStore(db.Model):
    name = db.StringProperty(required = True)
    registry = db.StringProperty(required = True)
    cache = db.BlobProperty()
    usepickle = db.BooleanProperty()

def ReadRecord(name, registry):
    cache_list = []
    query = IPStore.gql("WHERE name = :1 AND registry = :2", name, registry)
    for instance in query:
        cache = pickle.loads(instance.cache) \
                            if instance.usepickle else instance.cache
        cache_list.append(cache)

    return cache_list

def tWrite(name, registry, value, usepickle):
    store = IPStore(name = name,
                    registry = registry, 
                    cache = pickle.dumps(value, pickle.HIGHEST_PROTOCOL) \
                                            if usepickle else value, 
                    usepickle = usepickle)
    key = store.put()
    return key

def WriteRecord(name, registry, value, usepickle):
    DeleteRecord(name, registry)

    key = db.run_in_transaction(tWrite, name, registry, value, usepickle)
    return key

def tClean(query):
    query = db.get(query)
    db.delete(query)

def DeleteRecord(name, registry):
    query = IPStore.gql("WHERE name = :1 AND registry = :2", name, registry)
    qfetch = query.fetch(100)
    while len(qfetch) != 0:
        db.run_in_transaction(tClean, query)
        qfetch = query.fetch(100)

def Clear(registry):
    query = IPStore.gql("WHERE registry = :1", registry)
    qfetch = query.fetch(100)
    while len(qfetch) != 0:
        db.run_in_transaction(tClean, query)
        qfetch = query.fetch(100)

def ClearAll():
    if not memcache.flush_all(): #@UndefinedVariable
        logging.error('memcache flush_all failure.')
    db.run_in_transaction(tClean, IPStore.add())
