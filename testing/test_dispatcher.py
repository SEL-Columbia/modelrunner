# -*- coding: utf-8 -*-
import time
from threading import Thread
from modelrunner.settings import redis_connection
from modelrunner.redis_utils import enqueue_command, publish_command
from modelrunner.dispatcher import Dispatcher

class PrimaryCommandHandler:
    """
    Implement 'CommandHandler interface' for testing Dispatcher
    """

    def __init__(self):

        self.name = 'primary'
        self.count = 0
        self.jobs = {}
        self.dispatch = {
            'COMPLETE_JOB': self.complete_job
        }

    def enqueue_job(self, queue):
        job = {'id': self.count,
               'origin': self.name,
               'status': 'NEW'}

        command_dict = {'command': 'PROCESS_JOB', 'job': job}
        enqueue_command(redis_connection(), queue, command_dict)
        self.count += 1

    def kill_job(self, channel):
        command_dict = {'command': 'KILL_JOB'}
        publish_command(redis_connection(), channel, command_dict)

    def complete_job(self, command_dict):
        job = command_dict['job']
        job['status'] = 'COMPLETE'
        self.jobs[job['id']] = job


class WorkerCommandHandler:

    """
    Implement 'CommandHandler interface' for testing Dispatcher
    """

    def __init__(self, sleep_time=4):

        self.status = "STATUS_WAITING"
        self.jobs = {}
        self.sleep_time = sleep_time
        self.dispatch = {
            'PROCESS_JOB': self.process_job,
            'KILL_JOB': self.kill_job
        }

    def process_job(self, command_dict):
        job = command_dict['job']
        self.jobs[job['id']] = job
        job['status'] = 'PROCESSING'
        sleep_amount = 0
        while(sleep_amount < self.sleep_time):
            time.sleep(1)
            if job['status'] == 'KILLING':
                job['status'] = 'KILLED'
                break
            sleep_amount += 1

        if sleep_amount == self.sleep_time:
            job['status'] = 'PROCESSED'
            command_dict = {'command': 'COMPLETE_JOB', 'job': job}
            enqueue_command(redis_connection(), job['origin'], command_dict)

    def kill_job(self, command_dict):
        job_id = command_dict['job_id']
        self.jobs[job_id]['status'] = 'KILLING'


def test_primary_worker_scenario():

    primary_handler = PrimaryCommandHandler()
    worker_handler = WorkerCommandHandler()

    primary = Dispatcher(redis_connection(),
                         primary_handler,
                         "primary",
                         ["primary"])

    worker = Dispatcher(redis_connection(),
                        worker_handler,
                        "worker",
                        ["worker"])

    # start them up
    Thread(target=primary.wait_for_queue_commands).start()
    Thread(target=primary.wait_for_channel_commands).start()
    Thread(target=worker.wait_for_queue_commands).start()
    Thread(target=worker.wait_for_channel_commands).start()

    # submit a job
    primary_handler.enqueue_job("worker")

    # wait for it to complete
    sleep_time = 0
    while(sleep_time < worker_handler.sleep_time + 1):
        time.sleep(1)
        sleep_time += 1

    assert len(primary_handler.jobs) == 1 and\
           primary_handler.jobs[0]['status'] == 'COMPLETE'

    stop_queue_command = {'command': 'STOP_PROCESSING_QUEUE'}
    stop_channel_command = {'command': 'STOP_PROCESSING_CHANNELS'}

    publish_command(redis_connection(), "worker", stop_queue_command)
    publish_command(redis_connection(), "primary", stop_queue_command)
    publish_command(redis_connection(), "worker", stop_channel_command)
    publish_command(redis_connection(), "primary", stop_channel_command)
