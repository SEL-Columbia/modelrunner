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
from threading import Thread
from tornado.options import parse_command_line, parse_config_file


from modelrunner import config,\
                        PrimaryServer,\
                        Dispatcher,\
                        __version__

from modelrunner.settings import initialize,\
                                 redis_connection,\
                                 node_channel_name,\
                                 all_nodes_channel_name,\
                                 primary_queue_name

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

primary_handler = PrimaryServer(
                    config.options.primary_url,
                    config.options.data_dir)
channels = [node_channel_name(primary_handler.node.name),
            all_nodes_channel_name()]
primary = Dispatcher(
            redis_connection(),
            primary_handler,
            primary_queue_name(primary_handler.node.name),
            channels)

# continuously wait for jobs to complete and for status inquiries
Thread(target=primary.wait_for_queue_commands).start()
Thread(target=primary.wait_for_channel_commands).start()
