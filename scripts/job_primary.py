#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Primary Server

Script to wait for finished jobs from workers and fetch results

See config.py or pass --help to command for command line args
"""

import sys
import logging
from tornado.options import parse_command_line, parse_config_file

import modelrunner as mr
from modelrunner import config

# setup log
logger = logging.getLogger('modelrunner')

logger.info("modelrunner %s (Python %s)" %
            (mr.__version__,
             '.'.join(map(str, sys.version_info[:3]))))

# so we can load config via cmd line args
parse_command_line()
parse_config_file(config.options.config_file)

# get the command_ keys
command_dict = config.options.group_dict("model_command")

jm = mr.JobManager(config.options.redis_url,
                   config.options.primary_url,
                   config.options.worker_url,
                   config.options.data_dir,
                   command_dict,
                   config.options.worker_is_primary)

# continuously wait for jobs to complete
while(True):
    jm.wait_for_finished_jobs()
