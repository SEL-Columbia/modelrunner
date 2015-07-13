#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script for submitting job to system manually
"""

# setup config options
from modelrunner import config
from tornado.options import parse_command_line, parse_config_file

import modelrunner as mr

# so we can load config via cmd line args
parse_command_line()
parse_config_file(config.options.config_file)


jm = mr.JobManager(config.options.redis_url,
                   config.options.primary_url,
                   config.options.worker_url,
                   config.options.data_dir,
                   {})

job = mr.Job(config.options.model)
jm.add_update_job_table(job)
input_fh = open(config.options.input_file, 'r')
jm.enqueue(job, input_fh.read())
input_fh.close()

print("created job {}".format(job.uuid))