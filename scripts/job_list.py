#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script to list job data from Redis DB
"""

import csv
import sys
from modelrunner import config
import modelrunner
import modelrunner.settings

from tornado.options import parse_command_line, parse_config_file
from functools import reduce

# Prevents this script from failing when output is piped
# to another process
from signal import signal, SIGPIPE, SIG_DFL
signal(SIGPIPE, SIG_DFL)

# so we can load config via cmd line args
parse_command_line()
parse_config_file(config.options.config_file)

# initialize the global application settings
modelrunner.settings.initialize(config.options.redis_url)

jobs = modelrunner.Job.values()
if(len(jobs) > 0):
    # order descending
    jobs.sort(key=lambda job: job.created, reverse=True)
    job_dicts = [job.__dict__ for job in jobs]
    key_sets = [set(job_dict.keys()) for job_dict in job_dicts]
    all_keys = reduce(set.union, key_sets)

    dict_writer = csv.DictWriter(sys.stdout, list(all_keys))
    dict_writer.writer.writerow(list(all_keys))
    dict_writer.writerows(job_dicts)
