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
from threading import Thread

from modelrunner import config,\
                        WorkerServer,\
                        Dispatcher,\
                        __version__

from modelrunner.settings import initialize,\
                                 redis_connection,\
                                 job_queue_name,\
                                 node_channel_name,\
                                 all_nodes_channel_name

from tornado.options import parse_command_line, parse_config_file

# setup log
logger = logging.getLogger('modelrunner')

logger.info("modelrunner %s (Python %s)" %
            (__version__,
             '.'.join(map(str, sys.version_info[:3]))))

# so we can load config via cmd line args
parse_command_line()
parse_config_file(config.options.config_file)

# initialize the global application settings
initialize(config.options.redis_url)

# get the command_ keys
command_dict = config.options.group_dict("model_command")

worker_handler = WorkerServer(
                    config.options.worker_url,
                    config.options.data_dir,
                    config.options.model,
                    command_dict)
channels = [node_channel_name(worker_handler.node.name),
            all_nodes_channel_name()]
worker = Dispatcher(redis_connection(), 
                    worker_handler, 
                    job_queue_name(config.options.model),
                    channels)

# start listening for commands on queue and channels in bg
Thread(target=worker.wait_for_queue_commands).start()
Thread(target=worker.wait_for_channel_commands).start()
