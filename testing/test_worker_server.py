"""
Test the WorkerServer through various scenarios

The PrimaryServer is not necessary for testing
Though we need to server the input from some http server 
"""

import os
import shutil
from modelrunner import settings
from modelrunner import WorkerServer
from modelrunner import Job
from modelrunner import Worker
from modelrunner import manager

def make_config():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    # use file protocol so we don't need to bring up http servers
    test_model_path = os.path.join(base_dir, "models", "test.sh")
    model_command_dict = {"test": test_model_path, "test_2": test_model_path}
    config = {
              "primary_url": "file://",
              "worker_url":  "file://",
              "worker_data_dir": os.path.join(base_dir, "worker_data"),
              "primary_data_dir": os.path.join(base_dir, "primary_data"),
              "command_dict": model_command_dict
             }

    return config

def cleanup(config):
    
    redis_conn = settings.redis_connection()

    def delete_subdirs(d):
        for subdir in os.listdir(d):
            full_subdir = os.path.join(d, subdir)
            if os.path.isdir(full_subdir):
                shutil.rmtree(full_subdir, ignore_errors=True)

    delete_subdirs(config["primary_data_dir"])
    delete_subdirs(config["worker_data_dir"])

    for job in Job.values():
        del Job[job.uuid]

    for worker in Worker.values():
        del Worker[worker.name]

    # clear all remaining lists
    for list_key in redis_conn.keys():
        while redis_conn.lpop(list_key) is not None:
            pass

def _setup_job(model_name, job_name, config, input_file):

    # create a job to process
    job = Job(model_name)
    job.name = job_name
    job.primary_url = config["primary_url"]
    job.primary_data_dir = config["primary_data_dir"]
    job.status = Job.STATUS_QUEUED

    # copy test input.zip file to job dir
    job_data_dir = os.path.join(config["primary_data_dir"], job.uuid)
    if(not os.path.exists(job_data_dir)):
        os.mkdir(job_data_dir)

    # copy the template input_file to the job dir as the input.zip
    shutil.copy(os.path.join(config["primary_data_dir"], input_file),
                os.path.join(job_data_dir, "input.zip"))

    return job

def _enqueue_worker_job(job):
    """
    Submit job to queue for worker
    """
    settings.initialize()
    redis_conn = settings.redis_connection()
    queue_name = manager.job_queue_name(job.model)
    manager.enqueue_job(redis_conn, queue_name, job)

 
def test_run_to_complete():

    model_name = "test"
    config = make_config()    

    worker_server = WorkerServer(config["primary_url"], 
                                 config["worker_url"],
                                 config["worker_data_dir"],
                                 model_name,
                                 config["command_dict"])
    
    good_job = _setup_job(model_name, "processed_test", config, "good.zip")
    _enqueue_worker_job(good_job)

    # wait for job
    worker_server.wait_for_new_jobs()
    
    # check if job was processed 
    good_job = Job[good_job.uuid]
    assert good_job.status == Job.STATUS_PROCESSED

    cleanup(config)
