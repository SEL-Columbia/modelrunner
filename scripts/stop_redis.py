#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script to stop the configured redis instance
"""

from modelrunner import config
from modelrunner.settings import (
    initialize,
    redis_connection
)

# setup config options
from tornado.options import parse_command_line, parse_config_file

# so we can load config via cmd line args
parse_command_line()
parse_config_file(config.options.config_file)

# initialize the global application settings
initialize(config.options.redis_url)

# stop redis
redis_connection().shutdown()
