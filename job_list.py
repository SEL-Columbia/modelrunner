# -*- coding: utf-8 -*-
"""
Script to list job data from Redis DB
"""

import csv
import sys
import config
import job_manager

from tornado.options import parse_command_line, parse_config_file
from functools import reduce

# Prevents this script from failing when output is piped
# to another process
from signal import signal, SIGPIPE, SIG_DFL
signal(SIGPIPE, SIG_DFL)


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
    jobs = jm.get_jobs()
    if(len(jobs) > 0):
        # order descending
        jobs.sort(key=lambda job: job.created, reverse=True)
        job_dicts = [job.__dict__ for job in jobs]
        key_sets = [set(job_dict.keys()) for job_dict in job_dicts]
        all_keys = reduce(set.union, key_sets)

        dict_writer = csv.DictWriter(sys.stdout, list(all_keys))
        dict_writer.writer.writerow(list(all_keys))
        dict_writer.writerows(job_dicts)
