import tornado
import csv
import sys

# setup config options
import config
from tornado.options import parse_command_line, parse_config_file

import job_manager

if __name__ == "__main__":
    parse_config_file("config.ini")
    parse_command_line()
    # get the command_ keys
    command_dict = config.options.group_dict("model_command")

    jm = job_manager.JobManager(config.options.redis_url, 
                                config.options.primary_url, 
                                config.options.worker_url,
                                config.options.data_dir,
                                command_dict,
                                config.options.worker_is_primary)
    jobs =  jm.get_jobs()
    if(len(jobs) > 0):
        # order descending
        jobs.sort(key=lambda job: job.created, reverse=True)
        job_dicts = [job.__dict__ for job in jobs]
        job_keys = job_dicts[0].keys()
        dict_writer = csv.DictWriter(sys.stdout, job_keys)
        dict_writer.writer.writerow(job_keys)
        dict_writer.writerows(job_dicts)
