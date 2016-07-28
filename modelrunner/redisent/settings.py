# -*- coding: utf-8 -*-
"""
redisent package settings and initialization
"""

from . import RedisEntity
from redis import StrictRedis

def initialize(redis_connection=None, prefix=None):
    """
    Must be called before using redisent package
    """
    assert isinstance(redis_connection, StrictRedis),\
            "redis_connection must be instance of StrictRedis"
    #TODO:  Consider allowing _db to be a function so that it 
    #       can reference a pool
    RedisEntity._db = redis_connection
    RedisEntity._prefix = prefix
