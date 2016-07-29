#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script for submitting job to system manually
"""

import modelrunner
from modelrunner import config

# setup config options
from tornado.options import parse_command_line, parse_config_file

# so we can load config via cmd line args
parse_command_line()
parse_config_file(config.options.config_file)

# initialize the global application settings
modelrunner.settings.initialize(config.options.redis_url)

primary_server = modelrunner.PrimaryServer(config.options.primary_url,
                                           config.options.data_dir)
             
job = modelrunner.Job(config.options.model)
Job[job.uuid] = job
input_fh = open(config.options.input_file, 'r')
primary_server.enqueue(job, input_fh.read())
input_fh.close()

print("created job {}".format(job.uuid))
