import tornado
import redis

# setup config options
import config

from tornado.options import parse_command_line, parse_config_file

import job_manager


if __name__ == "__main__":

    parse_command_line()
    parse_config_file("config.ini")
    
    job = job_manager.Job(config.options.model)
    data_dir = config.options.data_dir
    input_file = config.options.input_file
    redis_url = config.options.redis_url
    primary_url = config.options.primary_url
    worker_url = config.options.worker_url

    # add job to redis and queue it
    jm = job_manager.JobManager(redis_url, primary_url, worker_url, data_dir, {})
   
    jm.add_update_job_table(job)
    input_fh = open(input_file, 'r')
    jm.enqueue(job, input_fh.read())
    input_fh.close()

    print "created job %s" % job.uuid
