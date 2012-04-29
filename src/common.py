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
        'ICANN':'http://ftp.apnic.net/stats/iana/delegated-iana-latest',
        'ARIN':'http://ftp.apnic.net/stats/arin/delegated-arin-latest',
        'APNIC':'http://ftp.apnic.net/stats/apnic/delegated-apnic-latest',
        'RIPE':'http://ftp.apnic.net/stats/ripe-ncc/delegated-ripencc-latest',
        'LACNIC':'http://ftp.apnic.net/stats/lacnic/delegated-lacnic-latest',
        'AFRINIC':'http://ftp.apnic.net/stats/afrinic/delegated-afrinic-latest'
        }

# データベースに保存されるデータのキー名
# "%s"部分は文字列に置き換えられる
reghash_keyname = '%s_HASH' # 例: 'APNIC_HASH'
countries_keyname = '%s_COUNTRIES' # 例 : 'APNIC_COUNTRIES', 'ALL_COUNTRIES'

# ----------------------------------------------------------------------------

class IPStore(db.Model):
    name = db.StringProperty(required = True)
    cache = db.BlobProperty()
    usepickle = db.BooleanProperty()

def CRC32Check(string):
    return zlib.crc32(string) & 0xFFFFFFFF
    
# memcacheからキャッシュを取得し、存在しなければデータストアから取得
# name : キャッシュ名
def get_cache(name):
    # memcacheから取得
    cache = memcache.get(name) #@UndefinedVariable
    if cache:
        logging.debug('Get cache success. "%s"' % name)
        return cache
    else:
        logging.debug('Get cache failure. "%s"' % name)
        
        # データストア内のキャッシュから取得
        logging.debug('Get DataStore "IPStore" start. "%s"' % name)
        query = db.GqlQuery("SELECT * FROM IPStore WHERE name = :1", name)
        record = query.get()
        if record:
            logging.debug('Get Datastore "IPStore" success. "%s"' % name)
            
            # memcache内に保存しなおしておく
            storecache = pickle.loads(record.cache) if record.usepickle else record.cache
            if memcache.set(name, storecache): #@UndefinedVariable
                logging.debug('Set cache success. "%s"' % name)
            else:
                logging.debug('Set cache failure. "%s"' % name)
            return storecache
        else:
            logging.error('Get Datastore "IPStore" failure. "%s"' % name)
            return None

# memcacheに保存し、バックアップとしてデータストアにも保存しておく。
# 古いバックアップは削除
# name : キャッシュ名
# value : キャッシュする値
# usepickle : valueをpickleで変換してキャッシュするか(True, False)
def set_cache(name, value, usepickle):
    # memcacheに保存
    if memcache.set(name, value): #@UndefinedVariable
        logging.debug('Set cache success. "%s"' % name)

        # 古いデータストアのバックアップを削除
        query = db.GqlQuery("SELECT * FROM IPStore WHERE name = :1", name)
        db.delete(query)

        # データストアにバックアップを保存
        logging.debug('Set DataStore "IPStore" start. "%s"' % name)
        store = IPStore(name = name, 
                cache = pickle.dumps(value, pickle.HIGHEST_PROTOCOL) if usepickle else value,
                usepickle = usepickle)
        store.put()
        logging.debug('Set Datastore "IPStore" success. "%s"' % name)
        return True
    else:
        logging.error('Set cache failure. "%s"' % name)
        return False

# 指定したキャッシュをmemcacheから削除し、データストアからも削除
# name : キャッシュ名
# fetch : 一回のループでいくつのデータストアのキャッシュを削除するか
def delete_cache(name, fetch = 100):
    logging.debug('Delete Cache Start. "%s' % name)
    
    query = db.GqlQuery("SELECT * FROM IPStore WHERE name = :1", name)
    qfetch = query.fetch(fetch)
    while len(qfetch) != 0:
        db.delete(qfetch)
        qfetch = query.fetch(fetch)
        
    # キャッシュの削除
    memcache.delete('%s' % name) #@UndefinedVariable
    
    logging.debug('Delete Cache Success. "%s' % name)

def Clear(registry):
    logging.info('DataStore "IPStore" cache and memcache clear start.')

    # 国名のキャッシュの削除
    countries_cache = get_cache(countries_keyname % registry)
    if countries_cache:
        for country in countries_cache:
            delete_cache(country)

    # レジストリのキャッシュの削除
    delete_cache(countries_keyname % registry, 10)
    
    # 全ての国名を保存したキャッシュを削除
    delete_cache(countries_keyname % "ALL", 10)
    
    logging.info('Cache clear end.')

def ClearAll():
    logging.info('Cache all clear start.')
    if not memcache.flush_all(): #@UndefinedVariable
        logging.error('memcache flush_all failure.')
    db.delete(IPStore.all())
    logging.info('Cache all clear end.')
