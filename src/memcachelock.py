#!/usr/bin/env python
# vim: set fileencoding=utf-8
# memcacheを使った排他制御
#
# 参照元
# http://d.hatena.ne.jp/eth0jp/20111109/1320782143
import time
import types

from google.appengine.api import memcache

UNLOCKED = 0
LOCKED = 1
KEY_PREFIX = "MemcacheLock. "

SLEEP_COUNT = 0.1
RETRY_COUNT = 5

class MemcacheLock():
    def __init__(self, key, key_prefix = KEY_PREFIX, sleep_time = SLEEP_COUNT, retry_count = RETRY_COUNT):
        self.key = key_prefix + key
        self.sleep_time = sleep_time
        self.retry_count = retry_count
        self.is_locked = False
        self.lock_value = None

    def lock(self):
        if self.is_locked:
            return True
        
        self.lock_value = memcache.incr(self.key, initial_value = 0) #@UndefinedVariable
        if self.lock_value == LOCKED:
            self.is_locked = True
            return True

        memcache.decr(self.key) #@UndefinedVariable
        return False

    def unlock(self):
        if self.is_locked:
            memcache.decr(self.key) #@UndefinedVariable
            self.is_locked = False
            return True
        return False

    def Synchronized(self, func, *args, **kwargs):
        for i in xrange(self.retry_count): #@UnusedVariable
            if self.lock():
                try:
                    return func(*args, **kwargs)
                finally:
                    self.unlock()
            time.sleep(self.sleep_time)
        raise Exception("Can't Lock: %s = %d" % (self.key, self.lock_value))

# デコレータ
def runSynchronized(**options):
    def deco(func):
        if type(func) != types.FunctionType:
            raise Exception("func isn't function")

        options['key'] = str(options.get('key'))
        if not options['key']:
            options['key'] = str(func.func_code.__hash__())

        def wrap(*args, **kwargs):
            memlock = MemcacheLock(**options)
            memlock.Synchronized(func, *args, **kwargs)
        return wrap
    return deco