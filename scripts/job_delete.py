#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script to delete list of \n delimited job ids
"""
import sys

# setup config options
from modelrunner import config
from tornado.options import parse_command_line, parse_config_file

import modelrunner
import modelrunner.settings

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
         
for uuid in [l.rstrip() for l in sys.stdin.readlines()]:
    modelrunner.settings.redis_connection().hdel("modelrunner:jobs", uuid)
