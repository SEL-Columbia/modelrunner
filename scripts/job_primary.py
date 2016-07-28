#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Primary Server

Script to wait for finished jobs from workers and fetch results

See config.py or pass --help to command for command line args
"""

import sys
import logging
import traceback
from tornado.options import parse_command_line, parse_config_file

import modelrunner
from modelrunner import config
import modelrunner.settings

# setup log
logger = logging.getLogger('modelrunner')

logger.info("modelrunner %s (Python %s)" %
            (modelrunner.__version__,
             '.'.join(map(str, sys.version_info[:3]))))

# so we can load config via cmd line args
parse_command_line()
parse_config_file(config.options.config_file)

# initialize the global application settings
modelrunner.settings.initialize(config.options.redis_url)

# get the command_ keys
command_dict = config.options.group_dict("model_command")

jm = modelrunner.JobManager(config.options.primary_url,
                            config.options.worker_url,
                            config.options.data_dir,
                            command_dict,
                            config.options.worker_is_primary)
 
# continuously wait for jobs to complete (reporting any exceptions)
while(True):
    try:
        jm.wait_for_finished_jobs()
    except:
        logger.error(traceback.format_exc())
