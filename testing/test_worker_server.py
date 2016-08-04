"""
Test the WorkerServer through various scenarios

The PrimaryServer is not necessary for testing
Though we need to server the input from some http server 
"""

import os
import shutil
import time
import threading
from modelrunner import settings
from modelrunner import WorkerServer
from modelrunner import Job
from modelrunner import Worker
from modelrunner import manager

# initialize
settings.initialize()
def make_config(model_name):

    base_dir = os.path.dirname(os.path.abspath(__file__))
    # use file protocol so we don't need to bring up http servers
    test_model_path = os.path.join(base_dir, "models", "test.sh")
    model_command_dict = {"test": test_model_path, "test_2": test_model_path}
    config = {
              "primary_url": "file://",
              "worker_url":  "file://",
              "worker_data_dir": os.path.join(base_dir, "worker_data"),
              "primary_data_dir": os.path.join(base_dir, "primary_data"),
              "model": model_name,
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

def _setup_job(config, job_name, input_file):

    # create a job to process
    job = Job(config["model"])
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
    redis_conn = settings.redis_connection()
    queue_name = manager.job_queue_name(job.model)
    manager.enqueue_job(redis_conn, queue_name, job)

def _worker_server(config):
    return WorkerServer(config["primary_url"], 
                        config["worker_url"],
                        config["worker_data_dir"],
                        config["model"],
                        config["command_dict"])

def test_run_good_bad():

    model_name = "test"
    config = make_config(model_name)    

    worker_server = _worker_server(config) 
    good_job = _setup_job(config, "processed_test", "good.zip")
    bad_job = _setup_job(config, "failed_test", "bad.zip")
    _enqueue_worker_job(good_job)
    _enqueue_worker_job(bad_job)

    # process good job
    worker_server.wait_for_new_jobs()
    good_job = Job[good_job.uuid]
    assert good_job.status == Job.STATUS_PROCESSED

    # process bad job
    try:
        worker_server.wait_for_new_jobs()
        assert False, "Exception should have been raised"
    except:
        bad_job = Job[bad_job.uuid]
        assert bad_job.status == Job.STATUS_FAILED

    cleanup(config)

def _publish(channel_name, message_dict, wait_time=0):
    """
    Test worker command processing
    """
    redis_conn = settings.redis_connection()
    if wait_time > 0:
        time.sleep(wait_time)

    manager.publish_message(redis_conn, channel_name, message_dict)
    
def _make_publish_function(config, command_dict, wait_time=0):
    """
    return a function that will publish a command_dict
    
    to be used as a target of a thread
    """
    worker_name = Worker.worker_name(config["worker_url"], config["model"])
    worker_channel = manager.worker_channel_name(worker_name)

    def publish_fun():
        _publish(worker_channel, command_dict, wait_time=wait_time)
    
    return publish_fun


def test_run_commands():

    model_name = "test"
    config = make_config(model_name)    

    worker_server = _worker_server(config) 
    killed_job = _setup_job(config, "killed_test", "good.zip")
    _enqueue_worker_job(killed_job)

    assert len(Worker.values()) == 0

    # start thread to publish a kill message in 2 seconds
    kill_command = {"command": "KILL", "job_uuid": killed_job.uuid}
    publish_kill_fun = _make_publish_function(config, kill_command, wait_time=2)
    threading.Thread(target=publish_kill_fun).start()

    worker_server.listen_for_commands()
    worker_server.wait_for_new_jobs()
    killed_job = Job[killed_job.uuid]
    assert killed_job.status == Job.STATUS_KILLED

    # have worker update status
    status_command = {"command": "STATUS"}
    publish_status = _make_publish_function(config, status_command)
    publish_status()
    
    # wait for a sec for the listener to write status
    time.sleep(1)
    worker = Worker[worker_server.worker.name]
    assert worker.status == Worker.STATUS_WAITING and \
           worker.model == model_name

    # stop the listener
    stop_command = {"command": "STOP"}
    publish_stop = _make_publish_function(config, stop_command)
    publish_stop()
 
    cleanup(config)
