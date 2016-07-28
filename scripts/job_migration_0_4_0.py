#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script to move all job logs to primary server

Migration 0.3.0 -> 0.4.0

Assumes that v0.4.0 of primary and workers of your modelrunner system 
are running
"""

import urllib2
import logging
from modelrunner import config
import modelrunner
import modelrunner.settings

from tornado.options import parse_command_line, parse_config_file

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

logger = logging.getLogger('modelrunner')

# Prevents this script from failing when output is piped
# to another process
from signal import signal, SIGPIPE, SIG_DFL
signal(SIGPIPE, SIG_DFL)

# so we can load config via cmd line args
parse_command_line()
parse_config_file(config.options.config_file)

def test_url(url):
    """
    Returns True if there's something at url, else False
    """
    try:
        urllib2.urlopen(job.log_url())
    except:
        return False
    return True

# initialize the global application settings
modelrunner.settings.initialize(config.options.redis_url)

# get the command_ keys
command_dict = config.options.group_dict("model_command")

jm = modelrunner.JobManager(config.options.primary_url,
                            config.options.worker_url,
                            config.options.data_dir,
                            command_dict,
                            config.options.worker_is_primary)
 
jobs = jm.get_jobs()

# get the log file for all jobs
for job in jobs:

    log_on_primary = test_url(job.log_url())
    job.on_primary = False
    log_on_worker = test_url(job.log_url())

    if not log_on_primary and log_on_worker:
        logger.info("job {} log not on primary".format(job.uuid))
        # then job.on_primary should be False and we need to retrieve it
        jm.add_update_job_table(job)
        # push message to primary to get data for job
        primary_queue = "modelrunner:queues:" + jm.primary_url
        settings.redis_connection.rpush(primary_queue, job.uuid)
