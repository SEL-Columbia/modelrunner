import tornado

# setup config options
import config
from tornado.options import parse_command_line, parse_config_file

import job_manager

if __name__ == "__main__":
    parse_command_line()
    parse_config_file("config.ini")
    # get the command_ keys
    command_dict = config.options.group_dict("model_command")

    jm = job_manager.JobManager(config.options.redis_url, 
                                config.options.primary_url, 
                                config.options.worker_url,
                                config.options.data_dir,
                                command_dict)

    # continuously wait for jobs to complete
    while(True):
        jm.wait_for_finished_jobs()

