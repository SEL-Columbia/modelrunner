# -*- coding: utf-8 -*-
"""
Module for global application settings and associated initialization functions

To be called from application entry points after configuration is read

Note:  This initializes the redisent sub-package as well
"""

from redis import StrictRedis
import redisent.settings

# _redis_connection = None

def redis_connection(redis_url="redis://@localhost:6379"):
    """
    Return the Redis connection to the url
    
    Once initialized, url cannot be reset
    """
    """
    global _redis_connection
    if _redis_connection is None:
        _redis_connection = StrictRedis.from_url(redis_url)
    return _redis_connection
    """

    # try handling via pool
    return StrictRedis.from_url(redis_url)

def initialize(redis_url="redis://@localhost:6379"):
    """
    Must be called before using modelrunner package
    """
    
    redisent.settings.initialize(redis_connection=redis_connection(redis_url),
                              prefix="modelrunner")
