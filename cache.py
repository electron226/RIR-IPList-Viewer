#!/usr/bin/env python
# vim: set fileencoding=utf-8
import logging

from google.appengine.api import memcache

def get_cache(key, key_prefix = '', namespace = None):
    if isinstance(key, list):
        return memcache.get_multi(key, key_prefix, namespace)
    else:
        return { key : memcache.get(key, namespace) }

def add_cache(key, value = None, time = 0, key_prefix = '', min_compress_len = 0, namespace = None):
    if isinstance(key, list):
        misslist = memcache.add_multi(key, time, key_prefix, min_compress_len, namespace)
        if len(misslist) != 0:
            logging.error("Memcache add_multi Failure.")
            for miss in misslist:
                logging.error("\n\t%s" % miss)
    else:
        if not memcache.add(key, value, time, min_compress_len, namespace):
            logging.error("Memcache add %s Failure." % key)

def set_cache(key, value = None, time = 0, key_prefix = '', min_compress_len = 0, namespace = None):
    if isinstance(key, list):
        misslist = memcache.set_multi(key, time, key_prefix, min_compress_len, namespace)
        if len(misslist) != 0:
            logging.error("Memcache set_multi Failure.")
            for miss in misslist:
                logging.error("\n\t%s" % miss)
    else:
        if not memcache.set(key, value, time, min_compress_len, namespace):
            logging.error("Memcache set %s Failure." % key)

def replace_cache(key, value = None, time = 0, key_prefix = '', min_compress_len = 0, namespace = None):
    addflag = False
    if isinstance(key, list):
        misslist = memcache.replace_multi(key, time, key_prefix, min_compress_len, namespace)
        count = len(misslist)
        if count == len(key):
            logging.error("Memcache replace_multi All Failure.")
            addflag = True
        elif count != 0:
            logging.error("Memcache replace_multi Failure.")
            for miss in misslist:
                logging.error("\n\t%s" % miss)
    else:
        if not memcache.replace(key, value, time, min_compress_len, namespace):
            logging.error("Memcache replace Failure.")
            addflag = True

    if addflag:
        logging.info("Memcache add process Start.")
        add_cache(key, value, time, key_prefix, min_compress_len, namespace)

def delete_cache(key, seconds = 0, key_prefix = '', namespace = None):
    if isinstance(key, list):
        if not memcache.delete_multi(key, seconds, key_prefix, namespace):
            logging.error("Memcache delete_multi Failure.")
    else:
        result = memcache.delete(key, seconds, namespace)
        if result == 0:
            logging.error("Memcache delete %s Failure." % key)
        elif result == 1:
            logging.warning("Memcache delete %s Missing." % key)
