# -*- coding: utf-8 -*-
"""
functions associated with implementing modelrunner 'protocol' via Redis

command dicts are serialized as json
"""

import logging
from .utils import json_dumps_datetime, json_loads_datetime

# setup log
logger = logging.getLogger('modelrunner')


def pop_command(redis_conn, queue_name, timeout=0):
    """
    *Blocking*

    Waits for command on redis queue
    timeout:  if 0, wait forever for item on queue, else seconds to timeout
    Returns command dict or None if timeout
    """

    result = redis_conn.blpop(queue_name, timeout=timeout)
    if result is None:
        # timedout
        return None

    command_dict = json_loads_datetime(result[1])
    return command_dict


def enqueue_command(redis_conn, queue_name, command_dict):
    """
    enqueue command on redis queue
    """
    logger.info(
        "adding command {} to queue {}".
        format(command_dict, queue_name))
    redis_conn.rpush(queue_name, json_dumps_datetime(command_dict))


def remove_command(redis_conn, queue_name, command_dict):
    """
    find and remove all matching commands from queue
    """
    result = redis_conn.lrange(queue_name, 0, -1)
    matches = filter(lambda d: d == command_dict,
                     [json_loads_datetime(item) for item in result])
    for match in matches:
        redis_conn.lrem(queue_name, 1, json_dumps_datetime(match))


def publish_command(redis_conn, channel_name, command_dict):
    """
    publish a message to a channel
    """
    redis_conn.publish(channel_name, json_dumps_datetime(command_dict))


def get_all_commands(redis_conn, queue_name):
    """
    get all command_dicts on queue
    """
    result = redis_conn.lrange(queue_name, 0, -1)
    return [json_loads_datetime(item) for item in result]


def pubsub_listen(pubsub):
    """
    generator that returns command_dict on subscribed pubsub object
    """

    assert pubsub.subscribed

    for raw_message in pubsub.listen():
        logger.info("message received {}".format(raw_message))

        # assume we subscribed and throw away anything other than messages
        if raw_message is not None and raw_message['type'] == 'message':
            message_dict = json_loads_datetime(raw_message['data'])
            yield message_dict
