#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Worker Server

Script to wait for jobs on a model specific queue (to be run on that model),
run them and report back to the Primary Server when the job status has changed

See config.py or pass --help to command for command line args
"""

import sys
import logging
import traceback

import modelrunner
from modelrunner import config

from tornado.options import parse_command_line, parse_config_file

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

worker_server = modelrunner.WorkerServer(config.options.primary_url,
                                         config.options.worker_url,
                                         config.options.data_dir,
                                         config.options.model,
                                         command_dict)

# start listening for messages from primary in background              
worker_server.listen_for_commands()

# continuously wait for jobs
while(True):
    try: 
        worker_server.wait_for_new_jobs()
    except:
        logger.error(traceback.format_exc())
