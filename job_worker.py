# -*- coding: utf-8 -*-
"""
Worker Server

Script to wait for jobs on a model specific queue (to be run on that model),
run them and report back to the Primary Server when the job status has changed

See config.py or pass --help to command for command line args
"""

# setup config options
import config
from tornado.options import parse_command_line, parse_config_file

import job_manager

if __name__ == "__main__":

    # so we can load config via cmd line args
    parse_command_line()
    parse_config_file(config.options.config_file)

    # get the command_ keys
    command_dict = config.options.group_dict("model_command")

    jm = job_manager.JobManager(config.options.redis_url,
                                config.options.primary_url,
                                config.options.worker_url,
                                config.options.data_dir,
                                command_dict,
                                config.options.worker_is_primary)

    # continuously wait for jobs
    while(True):
        jm.wait_for_new_jobs(config.options.model)
