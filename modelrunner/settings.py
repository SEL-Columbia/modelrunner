# -*- coding: utf-8 -*-
"""
Module for global application settings and associated initialization functions

To be called from application entry points after configuration is read
"""
import re
import redis

redis_connection = None

def init_redis_connection(redis_url):
    """
    Initialize the redis connection for the entire application
    """
    global redis_connection

    port_re = re.compile(r'(?<=:)\d+$')
    host_re = re.compile(r'^.*(?=:\d+$)')
    redis_host_match = host_re.search(redis_url)
    redis_port_match = port_re.search(redis_url)
    if(not redis_host_match or not redis_port_match):
        raise ValueError("invalid redis url: {}".format(redis_url))

    redis_connection = redis.Redis(host=redis_host_match.group(0),
                         port=redis_port_match.group(0))

