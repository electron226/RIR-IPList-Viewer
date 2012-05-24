#!/usr/bin/env python
# vim: set fileencoding=utf-8

##
# @file common.py
# @brief 全てのファイルで共通使用する
# @author khz

import pickle
import logging
import datetime

from google.appengine.api import memcache
from google.appengine.ext import db

## 割当リストの取得先
RIR = {
        'ARIN'    : 'http://ftp.apnic.net/stats/arin/delegated-arin-latest',
        'APNIC'   : 'http://ftp.apnic.net/stats/apnic/delegated-apnic-latest',
        'RIPE'    : 'http://ftp.apnic.net/stats/ripe-ncc/delegated-ripencc-latest',
        'LACNIC'  : 'http://ftp.apnic.net/stats/lacnic/delegated-lacnic-latest',
        'AFRINIC' : 'http://ftp.apnic.net/stats/afrinic/delegated-afrinic-latest',
        }

## 取得先の担当地域
RIREXP = {
        'ARIN'    : ['北アメリカ'],
        'APNIC'   : ['アジア', '太平洋'],
        'RIPE'    : ['ヨーロッパ', '中東', '中央アジア'],
        'LACNIC'  : ['ラテンアメリカ', 'カリブ海'],
        'AFRINIC' : ['アフリカ'], 
        }

## 割当先から取得したデータの一時保存用キー。文字列の置き換え機能を使う。
MEMCACHE_CONTENT    = '%s_CONTENT'

## 最後の更新日時の一時保存用
MEMCACHE_LASTUPDATE = 'LASTUPDATE'

## ハッシュキー名
HASH_KEYNAME      = 'HASH'

## 国名一覧のキー名
COUNTRIES_KEYNAME = 'COUNTRIES'

## IP一覧を保存する
## memcacheの最大保存期間(秒)
## 最高期間: 1ヶ月
memcache_time = (129600)

# ----------------------------------------------------------------------------

##
# @brief リストを特定サイズごとに分割。
#
# @param seq  分割するリスト
# @param size 分割するサイズ
#
# @return 分割されたリストを含んだリスト
# @throw  ValueError 最初の引数の値がリスト型ではない
def Split_Seq(seq, size):
    if isinstance(seq, list):
        return [seq[i : i + size] for i in xrange(0, len(seq), size)]
    raise ValueError("Split_Seq(): argument error.")

# ----------------------------------------------------------------------------
# 更新日時関係のクラス・関数群
# ----------------------------------------------------------------------------

##
# @brief レジストリの更新日時を記録するのに使うデータモデル。
class UpdateDate(db.Model):
    registry = db.StringProperty(required = True)
    time = db.DateTimeProperty(required = True)

##
# @brief 最後の更新日時を取得。
#
# @return datetimeオブジェクト
def GetLastUpdateDate():
    query = UpdateDate.gql("ORDER BY time DESC")
    date = query.get()

    return date

##
# @brief 現在のUTC時間を取得し、データストアに記録。トランザクション処理に使用。
# 
# @param registry 更新するレジストリ名
#
# @return 格納されたエンティティのKey
def tWriteDate(registry):
    time = datetime.datetime.utcnow()
    dateobj = UpdateDate(registry = registry, time = time)
    key = dateobj.put()

    return key

##
# @brief 更新日時を更新。
#
# @param registry 更新するレジストリ名
#
# @return 格納されたエンティティのKey
def WriteDate(registry):
    DeleteDate(registry)
    key = db.run_in_transaction(tWriteDate, registry)

    return key

##
# @brief 指定したレジストリの更新日時の記録を削除。
# 
# @param registry 削除するレジストリ
#
# @return なし
def DeleteDate(registry):
    query = UpdateDate.gql("WHERE registry = :1", registry)
    for one_query in query:
        db.run_in_transaction(tDelete, one_query)

    # memcacheにある最終更新日時を削除しておく
    memcache.delete(MEMCACHE_LASTUPDATE) #@UndefinedVariable

# ----------------------------------------------------------------------------
# IP一覧の保存・読み込みなどに使用するクラス・関数群
# ----------------------------------------------------------------------------

##
# @brief IP割当一覧を保存するデータモデル。
class IPStore(db.Model):
    name      = db.StringProperty(required = True)
    registry  = db.StringProperty(required = True)
    cache     = db.BlobProperty()
    usepickle = db.BooleanProperty()

# 指定したキーでデータストア(IPStore)からデータを取得
# 取得したデータはリストで返す
# name : 名前
# registry : レジストリ
##
# @brief 指定したキーでデータストアからデータを取得。
#
# @param kwargs 辞書型の可変長引数
#               キー名にname(名前), registry(レジストリ名)のどちらか必要。
#
# @return 引数で指定
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

##
# @brief memcacheで検索し、なければデータストアから取得。
#
#        最初にmemcacheを検索して、データがあればそれを返す。
#        データを取得できなければデータストアから取得。
#        データストアから取得したデータはmemcacheに再登録する。
#
# @param keys 取得するキー名のリスト
# @param prefix memcacheで使用するキー名の前につける文字列、
#               データストアではレジストリ名として使われる。
#
# @return 取得したデータの辞書型。引数で使ったキー名に入っている。
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

##
# @brief データストアに記録。トランザクション処理に使用。
#
# @param name 名前
# @param registry レジストリ名
# @param value 記録する値
# @param usepickle valueを直列化して保存するかどうか(True, False)
#
# @return 格納したエンティティのキー
def tWrite(name, registry, value, usepickle):
    store = IPStore(name = name,
                    registry = registry, 
                    cache = pickle.dumps(value, pickle.HIGHEST_PROTOCOL) \
                                            if usepickle else value, 
                    usepickle = usepickle)
    key = store.put()
    return key

##
# @brief データストアのデータを更新する。
#
# @param name 名前
# @param registry レジストリ名
# @param value 記録する値
# @param usepickle valueを直列化して保存するかどうか(True, False)
#
# @return 格納したエンティティのキー
def WriteRecord(name, registry, value, usepickle):
    DeleteRecord(name = name, registry = registry)

    key = db.run_in_transaction(tWrite, name, registry, value, usepickle)

    return key

##
# @brief クエリを受け取り、クエリのデータを削除。
#
# @param query クエリ
#
# @return なし
def tDelete(query):
    db.delete(query)

##
# @brief データストアからデータを削除
#
# @param kwargs 辞書型の可変長引数。
#               キーにname(名前), registry(レジストリ名)のどちらかが必須。
#
# @return なし
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

##
# @brief memcacheと全てのデータストアのデータを削除
#
# @return なし
def ClearAll():
    if not memcache.flush_all(): #@UndefinedVariable
        logging.error('memcache flush_all failure.')
    db.delete(IPStore.all())
    db.delete(UpdateDate.all())

# ----------------------------------------------------------------------------
