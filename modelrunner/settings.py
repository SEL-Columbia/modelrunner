# -*- coding: utf-8 -*-
"""
Module for global application settings and associated initialization functions

To be called from application entry points after configuration is read
"""
from redis import StrictRedis

_redis_connection = None
_redis_url="localhost:6379"

def redis_connection():
    """
    Return the Redis connection to the url
    """
    global _redis_connection
    if _redis_connection is None:
        _redis_connection = StrictRedis.from_url(_redis_url)
    return _redis_connection
