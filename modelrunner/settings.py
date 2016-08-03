# -*- coding: utf-8 -*-
"""
Module for global application settings and associated initialization functions

To be called from application entry points after configuration is read

Note:  This initializes the redisent sub-package as well
"""

from redis import StrictRedis
import redisent.settings

def redis_connection(redis_url="redis://@localhost:6379"):
    """
    Return the Redis connection to the url
    
    This uses a pooled connection
    """

    return StrictRedis.from_url(redis_url)

def initialize(redis_url="redis://@localhost:6379"):
    """
    Must be called before using modelrunner package
    """
    
    redisent.settings.initialize(redis_connection=redis_connection(redis_url),
                              prefix="modelrunner")
