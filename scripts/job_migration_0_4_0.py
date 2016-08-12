#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script to move all job logs to primary server

Migration 0.3.0 -> 0.4.0

Assumes that v0.4.0 of primary and workers of your modelrunner system
are running
"""

from signal import signal, SIGPIPE, SIG_DFL
import urllib2
import logging
from modelrunner import (
    config,
    Job
)

from modelrunner.settings import (
    initialize,
    primary_queue_name,
    redis_connection
)

from tornado.options import parse_command_line, parse_config_file

logger = logging.getLogger('modelrunner')

# Prevents this script from failing when output is piped
# to another process
signal(SIGPIPE, SIG_DFL)


def test_url(url):
    """
    Returns True if there's something at url, else False
    """
    try:
        urllib2.urlopen(job.log_url())
    except:
        return False
    return True


# so we can load config via cmd line args
parse_command_line()
parse_config_file(config.options.config_file)

# initialize the global application settings
initialize(config.options.redis_url)

jobs = Job.values()

# get the log file for all jobs
for job in jobs:

    log_on_primary = test_url(job.log_url())
    job.on_primary = False
    log_on_worker = test_url(job.log_url())

    if not log_on_primary and log_on_worker:
        logger.info("job {} log not on primary".format(job.uuid))
        # then job.on_primary should be False and we need to retrieve it
        Job[job.uuid] = job
        # push message to primary to get data for job
        primary_queue = primary_queue_name(job.primary_url)
        redis_connection.rpush(primary_queue, job.uuid)
