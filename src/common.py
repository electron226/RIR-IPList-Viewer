#!/usr/bin/env python
# vim: set fileencoding=utf-8
import pickle
import logging
import datetime

from google.appengine.api import memcache
from google.appengine.ext import db

# ----------------------------------------------------------------------------
# 取得先
RIR = {
        'ARIN'    : 'http://ftp.apnic.net/stats/arin/delegated-arin-latest',
        'APNIC'   : 'http://ftp.apnic.net/stats/apnic/delegated-apnic-latest',
        'RIPE'    : 'http://ftp.apnic.net/stats/ripe-ncc/delegated-ripencc-latest',
        'LACNIC'  : 'http://ftp.apnic.net/stats/lacnic/delegated-lacnic-latest',
        'AFRINIC' : 'http://ftp.apnic.net/stats/afrinic/delegated-afrinic-latest',
        }

# 取得先の担当地域
RIREXP = {
        'ARIN'    : ['北アメリカ'],
        'APNIC'   : ['アジア', '太平洋'],
        'RIPE'    : ['ヨーロッパ', '中東', '中央アジア'],
        'LACNIC'  : ['ラテンアメリカ', 'カリブ海'],
        'AFRINIC' : ['アフリカ'], 
        }

# memcache用
# "%s"部分は文字列に置き換えられる
MEMCACHE_CONTENT    = '%s_CONTENT' # 取得したデータの一時保存用
MEMCACHE_LASTUPDATE = 'LASTUPDATE' # 最後の更新日時の一時保存用

# データベースに保存されるデータのキー名
HASH_KEYNAME      = 'HASH'
COUNTRIES_KEYNAME = 'COUNTRIES'

# IP一覧を保存する
# memcacheの最大保存期間(秒)
# 最高期間: 1ヶ月
memcache_time = (129600)

# ----------------------------------------------------------------------------

# リストをsizeごとに分ける
# seq : list
# size : 分割サイズ
def Split_Seq(seq, size):
    return [seq[i : i + size] for i in xrange(0, len(seq), size)]

# ----------------------------------------------------------------------------

def MemcacheDelete(keys, seconds = 0, key_prefix = "", namespace = None):
    if isinstance(keys, list):
        error = memcache.delete_multi(keys, seconds, key_prefix, namespace)

        return error
    else:
        error = memcache.delete(keys, seconds) #@UndefinedVariable
        if error == memcache.DELETE_NETWORK_FAILURE: #@UndefinedVariable
            logging.error("MemcacheDelete(): Network failure.")

            return False
        return True

# ----------------------------------------------------------------------------

class UpdateDate(db.Model):
    registry = db.StringProperty(required = True)
    time = db.DateTimeProperty(required = True)

def GetLastUpdateDate():
    query = UpdateDate.gql("ORDER BY time DESC")
    date = query.get()

    return date

def tWriteDate(registry):
    time = datetime.datetime.utcnow()
    dateobj = UpdateDate(registry = registry, time = time)
    key = dateobj.put()

    return key

def WriteDate(registry):
    DeleteDate(registry)
    key = db.run_in_transaction(tWriteDate, registry)

    return key

def DeleteDate(registry):
    query = UpdateDate.gql("WHERE registry = :1", registry)
    for one_query in query:
        db.run_in_transaction(tDelete, one_query)

    # memcacheにある最終更新日時を削除しておく
    MemcacheDelete(MEMCACHE_LASTUPDATE) #@UndefinedVariable

# ----------------------------------------------------------------------------

class IPStore(db.Model):
    name      = db.StringProperty(required = True)
    registry  = db.StringProperty(required = True)
    cache     = db.BlobProperty()
    usepickle = db.BooleanProperty()

def ReadRecord(**kwargs):
    name = kwargs.get('name')
    registry = kwargs.get('registry')

    cache_list = []

    if name and registry:
        query = IPStore.gql("WHERE name = :1 AND registry = :2", name, registry)
    elif name and not registry:
        query = IPStore.gql("WHERE name = :1", name)
    elif not name and registry:
        query = IPStore.gql("WHERE registry = :1", registry)

        # registryのみ使用する場合、別処理
        for instance in query:
            # 国名データ以外はスキップ
            if len(instance.name) != 2:
                continue

            cache = pickle.loads(instance.cache) \
                                if instance.usepickle else instance.cache
            cache_list.append(cache)

        return cache_list
    else:
        raise ValueError('ReadRecord() argument error.')

    # registryのみ以外を使用する場合
    for instance in query:
        cache = pickle.loads(instance.cache) \
                            if instance.usepickle else instance.cache
        cache_list.append(cache)

    return cache_list

def GetMultiData(keys, prefix):
    cachedict = memcache.get_multi(keys, prefix) #@UndefinedVariable

    keyset = set(keys)
    cacheset = set(cachedict.keys()) 
    
    # 全て取得できなかった場合、データストアから再取得
    if not keyset.issubset(cacheset):
        logging.warning("GetMultiData(): No Get memcache, \
                Get DataStore. (keys: %s, prefix: %s)" % (keys, prefix))

        # 取得できなかったkey一覧を取得
        notget = keyset.difference(cacheset)

        # データストアから取得、memcacheに再設定を行う
        reload_data = {}
        for notkey in notget:
            recordlist = ReadRecord(name = notkey, registry = prefix)
            if len(recordlist) == 0:
                # データストアから取得できなかった
                raise RuntimeError('Not Record From DataStore. key: %s' % notkey)
            elif len(recordlist) > 1:
                # データストアから取得できたがデータが一つではない
                logging.warning(
                    "Not Get Record Length 1. Use first data. key: %s" % notkey)

            reload_data[notkey] = recordlist[0]

        # memcacheに再設定
        if len(memcache.set_multi(reload_data, memcache_time, prefix)) == 0: #@UndefinedVariable
            logging.warning("GetMultiData(): Set memcache again.")
        else:
            logging.warning("GetMultiData(): Set memcache failure.")

        # memcache.get_multiで取得したデータにデータストアから取得したデータを追加
        for key, value in reload_data.iteritems():
            if not cachedict.has_key(key):
                cachedict[key] = value
            else:
                # 既に同じキーのデータが存在している
                raise RuntimeError(
                    'GetMultiData(): Already Get Key Data. key: %s' % key)
        
    return cachedict

def tWrite(name, registry, value, usepickle):
    store = IPStore(name = name,
                    registry = registry, 
                    cache = pickle.dumps(value, pickle.HIGHEST_PROTOCOL) \
                                            if usepickle else value, 
                    usepickle = usepickle)
    key = store.put()
    return key

def WriteRecord(name, registry, value, usepickle):
    DeleteRecord(name = name, registry = registry)

    key = db.run_in_transaction(tWrite, name, registry, value, usepickle)

    return key

def tDelete(query):
    db.delete(query)

def DeleteRecord(**kwargs):
    name = kwargs.get('name')
    registry = kwargs.get('registry')

    if name and registry:
        query = IPStore.gql("WHERE name = :1 AND registry = :2", name, registry)
    elif name and not registry:
        query = IPStore.gql("WHERE name = :1", name)
    elif not name and registry:
        query = IPStore.gql("WHERE registry = :1", registry)
    else:
        raise ValueError('DeleteRecord() argument error.')

    qfetch = query.fetch(100)
    while len(qfetch) != 0:
        for one_query in qfetch:
            db.run_in_transaction(tDelete, one_query)
        qfetch = query.fetch(100)

def ClearAll():
    if not memcache.flush_all(): #@UndefinedVariable
        logging.error('memcache flush_all failure.')
    for registry in RIR:
        DeleteRecord(registry = registry)

# ----------------------------------------------------------------------------
