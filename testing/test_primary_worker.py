"""
Test the WorkerServer through various scenarios

The PrimaryServer is not necessary for testing
Though we need to server the input from some http server
"""

import os
import shutil
import time
from threading import Thread
from modelrunner.settings import initialize,\
                                 redis_connection,\
                                 job_queue_name,\
                                 node_channel_name,\
                                 primary_queue_name,\
                                 all_nodes_channel_name,\
                                 worker_name

from modelrunner.redis_utils import enqueue_command,\
                                    publish_command,\
                                    get_all_commands

from modelrunner import PrimaryServer, WorkerServer, Job, Node, Dispatcher

# initialize
initialize()


# <helpers>
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

    redis_conn = redis_connection()

    def delete_subdirs(d):
        for subdir in os.listdir(d):
            full_subdir = os.path.join(d, subdir)
            if os.path.isdir(full_subdir):
                shutil.rmtree(full_subdir, ignore_errors=True)

    delete_subdirs(config["primary_data_dir"])
    delete_subdirs(config["worker_data_dir"])

    for job in Job.values():
        del Job[job.uuid]

    for node in Node.values():
        del Node[node.name]

    # clear all remaining lists
    for list_key in redis_conn.keys():
        while redis_conn.lpop(list_key) is not None:
            pass


def setup_queued_job(config, job_name, input_file):

    # create a job to process
    job = Job(
            model=config["model"],
            name=job_name,
            primary_url=config["primary_url"],
            primary_data_dir=config["primary_data_dir"])

    # store it
    Job[job.uuid] = job

    # copy test input.zip file to job dir
    job_data_dir = os.path.join(config["primary_data_dir"], job.uuid)
    if(not os.path.exists(job_data_dir)):
        os.mkdir(job_data_dir)

    # copy the template input_file to the job dir as the input.zip
    shutil.copy(os.path.join(config["primary_data_dir"], input_file),
                os.path.join(job_data_dir, "input.zip"))

    return job


def setup_processed_job(config, job_name):

    # create a job to process
    job = Job(
            model=config["model"],
            name=job_name,
            status=Job.STATUS_PROCESSED,
            primary_url=config["primary_url"],
            worker_url=config["worker_url"],
            primary_data_dir=config["primary_data_dir"],
            worker_data_dir=config["worker_data_dir"],
            on_primary=False)

    # store it
    Job[job.uuid] = job

    # copy test output.zip file to job dir
    job_data_dir = os.path.join(config["worker_data_dir"], job.uuid)
    if(not os.path.exists(job_data_dir)):
        os.mkdir(job_data_dir)

    # copy the template output file and job_log.txt file to job data dir
    shutil.copy(os.path.join(config["worker_data_dir"], "output.zip"),
                os.path.join(job_data_dir, "output.zip"))
    shutil.copy(os.path.join(config["worker_data_dir"], "job_log.txt"),
                os.path.join(job_data_dir, "job_log.txt"))

    return job


def enqueue_worker_job(job):
    """
    Submit job to queue for worker
    """
    redis_conn = redis_connection()
    queue_name = job_queue_name(job.model)
    command_dict = {'command': 'PROCESS_JOB', 'job_uuid': job.uuid}
    enqueue_command(redis_conn, queue_name, command_dict)


def enqueue_complete_job(job):
    """
    Submit job to queue for worker
    """
    redis_conn = redis_connection()
    queue_name = primary_queue_name(job.primary_url)
    command_dict = {'command': 'COMPLETE_JOB', 'job_uuid': job.uuid}
    enqueue_command(redis_conn, queue_name, command_dict)


def get_worker(config):
    worker_handler = WorkerServer(
                        config["worker_url"],
                        config["worker_data_dir"],
                        config["model"],
                        config["command_dict"])
    channels = [node_channel_name(worker_handler.node.name),
                all_nodes_channel_name()]
    worker = Dispatcher(redis_connection(),
                        worker_handler,
                        job_queue_name(config["model"]),
                        channels)
    return worker


def get_primary(config):
    primary_handler = PrimaryServer(
                        config["primary_url"],
                        config["primary_data_dir"])
    channels = [node_channel_name(primary_handler.node.name),
                all_nodes_channel_name()]
    primary = Dispatcher(
                redis_connection(),
                primary_handler,
                primary_queue_name(primary_handler.node.name),
                channels)
    return primary


def publish(channel_name, command_dict, wait_time=0):
    """
    Test worker command processing
    """
    redis_conn = redis_connection()
    if wait_time > 0:
        time.sleep(wait_time)

    publish_command(redis_conn, channel_name, command_dict)


def make_publish_function(channel_name, command_dict, wait_time=0):
    """
    return a function that will publish a command_dict

    to be used as a target of a thread
    """
    def publish_fun():
        publish(channel_name, command_dict, wait_time=wait_time)

    return publish_fun

# </helpers>


# <tests>
def test_run_good_bad():

    model_name = "test"
    config = make_config(model_name)

    worker = get_worker(config)
    sleep8_job = setup_queued_job(config, "processed_test", "sleep_8.zip")
    bad_job = setup_queued_job(config, "failed_test", "bad.zip")
    enqueue_worker_job(sleep8_job)
    enqueue_worker_job(bad_job)

    # process good and bad jobs in bg thread
    tq = Thread(target=worker.wait_for_queue_commands)
    tq.start()

    # give it some time
    time.sleep(10)

    assert Job[sleep8_job.uuid].status == Job.STATUS_PROCESSED
    assert Job[bad_job.uuid].status == Job.STATUS_FAILED

    # stop waiting
    stop_queue_command = {'command': 'STOP_PROCESSING_QUEUE'}
    enqueue_command(
        redis_connection(),
        job_queue_name(model_name),
        stop_queue_command)

    tq.join()

    cleanup(config)


def test_run_commands():

    model_name = "test"
    config = make_config(model_name)

    name = worker_name(config["worker_url"], config["model"])
    worker_channel = node_channel_name(name)

    worker = get_worker(config)
    killed_job = setup_queued_job(config, "killed_test", "sleep_8.zip")
    enqueue_worker_job(killed_job)

    assert len(Node.values()) == 0

    # start thread to publish a kill message in 2 seconds
    kill_command = {"command": "KILL_JOB", "job_uuid": killed_job.uuid}
    publish_kill_fun = make_publish_function(
                        worker_channel,
                        kill_command,
                        wait_time=2)

    Thread(target=publish_kill_fun).start()

    tq = Thread(target=worker.wait_for_queue_commands)
    tq.start()
    tc = Thread(target=worker.wait_for_channel_commands)
    tc.start()

    # give it some time
    time.sleep(4)

    assert Job[killed_job.uuid].status == Job.STATUS_KILLED

    # have worker update status
    status_command = {"command": "UPDATE_STATUS"}
    publish(worker_channel, status_command)

    # give it a sec
    time.sleep(1)

    node = Node[name]
    assert node.status == Node.STATUS_WAITING and \
        node.model == model_name

    # stop both queue and channel threads
    stop_queue_command = {'command': 'STOP_PROCESSING_QUEUE'}
    stop_channel_command = {'command': 'STOP_PROCESSING_CHANNELS'}
    publish(worker_channel, stop_queue_command)
    publish(worker_channel, stop_channel_command)
    tq.join()
    tc.join()

    cleanup(config)


def test_primary_enqueue_kill():
    """ test enqueue, kill """
    model_name = "test"
    config = make_config(model_name)

    primary = get_primary(config)

    # create a job to process
    job = Job(model_name)
    job.name = "primary_test"
    job_input_url = "{}{}/sleep_8.zip".format(
                        config["primary_url"],
                        config["primary_data_dir"])

    # enqueue job
    primary.command_handler.enqueue(job, job_data_url=job_input_url)

    assert Job[job.uuid].status == Job.STATUS_QUEUED
    path_to_input = os.path.join(
                        config["primary_data_dir"],
                        job.uuid,
                        "input.zip")
    assert os.path.exists(path_to_input)

    def get_queued_commands():
        return get_all_commands(
                redis_connection(),
                job_queue_name(model_name))

    commands = get_queued_commands()
    assert len(commands) == 1 and commands[0]['job_uuid'] == job.uuid

    # kill the job
    primary.command_handler.kill_job(job)
    assert Job[job.uuid].status == Job.STATUS_KILLED

    commands = get_queued_commands()
    assert len(commands) == 0

    cleanup(config)


def test_primary_complete():
    """ test compete job """
    model_name = "test"
    config = make_config(model_name)

    primary = get_primary(config)
    name = config["primary_url"]
    primary_channel = node_channel_name(name)

    # start primary
    tq = Thread(target=primary.wait_for_queue_commands)
    tq.start()
    tc = Thread(target=primary.wait_for_channel_commands)
    tc.start()

    # add job and make sure it gets processed
    job = setup_processed_job(config, "processed")
    enqueue_complete_job(job)

    # wait for it
    time.sleep(1)

    assert Job[job.uuid].status == Job.STATUS_COMPLETE
    path_to_output = os.path.join(
                        config["primary_data_dir"],
                        job.uuid,
                        "output.zip")
    assert os.path.exists(path_to_output)

    # stop both queue and channel threads
    stop_queue_command = {'command': 'STOP_PROCESSING_QUEUE'}
    stop_channel_command = {'command': 'STOP_PROCESSING_CHANNELS'}
    publish(primary_channel, stop_queue_command)
    publish(primary_channel, stop_channel_command)

    tq.join()
    tc.join()

    cleanup(config)
