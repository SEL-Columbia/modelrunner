#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script to delete list of \n delimited job ids
"""
import sys

import modelrunner
from modelrunner import config

# setup config options
from tornado.options import parse_command_line, parse_config_file

# so we can load config via cmd line args
parse_command_line()
parse_config_file(config.options.config_file)

# initialize the global application settings
modelrunner.settings.initialize(config.options.redis_url)

for uuid in [l.rstrip() for l in sys.stdin.readlines()]:
    del modelrunner.Job[uuid]
