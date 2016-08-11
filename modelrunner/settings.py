# -*- coding: utf-8 -*-
"""
Module for global application settings and associated initialization functions

To be called from application entry points after configuration is read

Note:  This initializes the redisent sub-package as well
"""

from redis import StrictRedis
import redisent.settings

_redis_connection = None

def redis_connection(redis_url="redis://@localhost:6379"):
    """
    Return the Redis connection to the url

    This returns a pooled connection (see http://bit.ly/2axtR2k)
    """
    global _redis_connection
    if _redis_connection is None:
        _redis_connection = StrictRedis.from_url(redis_url)

    return _redis_connection

def initialize(redis_url="redis://@localhost:6379"):
    """
    Must be called before using modelrunner package
    """

    redisent.settings.initialize(redis_connection=redis_connection(redis_url),
                              prefix="modelrunner")

def job_queue_name(model_name):
    return "modelrunner:queues:{}".format(model_name)

def primary_queue_name(primary_name):
    return "modelrunner:queues:{}".format(primary_name)

def node_channel_name(node_name):
    return "modelrunner:channels:{}".format(node_name)

def all_nodes_channel_name():
    return "modelrunner:channels:nodes"

def worker_name(node_url, model):
    return "{};{}".format(node_url, model)
