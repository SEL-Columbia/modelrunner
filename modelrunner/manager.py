# -*- coding: utf-8 -*-
"""
Module for managing job running and sync between primary and workers
"""

import os
import datetime
import json
import redis
import re
import pickle
import logging
import threading
import subprocess
import psutil
from zipfile import ZipFile
from modelrunner.utils import fetch_file_from_url, zipdir

from modelrunner import settings
from modelrunner.redisent import RedisEntity
from modelrunner import Job

# setup log
logger = logging.getLogger('modelrunner')

class WaitForCommand(threading.Thread):
    """
    Thread used by WorkerServer to wait for commands while process is running

    Attributes:
        worker_queue (str):  name of worker queue to listen for commands
        popen_proc (subprocess):  subprocess running job to be managed
        job_uuid (str):  uuid of job managed by this thread

    """

    def __init__(self, worker_queue, popen_proc, job_uuid):
        threading.Thread.__init__(self)
        self.worker_queue = worker_queue
        self.popen_proc = popen_proc
        self.job_uuid = job_uuid
        self.killed = False

    def run(self):
        """
        Wait for commands associated with this job

        handle case where kill message for "old" job is submitted
        by pulling off messages until one associated with 'this' job is found
        (otherwise, we might kill new jobs via messages for old jobs)

        When job is completed, a BREAK message should be sent to
        stop this thread.
        """

        logger.info("WaitForCommand of job {} running with pid {}".format(self.job_uuid, self.popen_proc.pid))

        # check for other threads
        existing_threads = filter(lambda x: isinstance(x, WaitForCommand), 
                                  threading.enumerate())
        if len(existing_threads) > 1:
            logger.warning("More than 1 thread waiting on queue {}".\
                           format(self.worker_queue))

        while(True):
            # block on queue and unpickle message dict when it arrives
            raw_message = settings.redis_connection().blpop(self.worker_queue)[1]
            message = pickle.loads(raw_message)
            job_uuid = message['job_uuid']
            command = message['command']
            logger.info("Received command {} for job_uuid {} on queue {}".\
                        format(command, job_uuid, self.worker_queue))

            if(job_uuid == self.job_uuid):
                if(command == "KILL"):
                    # if subprocess spawned any children, we need to kill 
                    # them first
                    parent = psutil.Process(self.popen_proc.pid)
                    for child in parent.children(recursive=True):
                        logger.info("Killing child pid {}".format(child.pid))
                        child.kill()
                    logger.info("Killing parent pid {}".format(parent.pid))
                    parent.kill()
                    # TODO:  Any reason to wait on kill?
                    self.killed = True

                if(command == "BREAK"):
                    logger.info("Stop waiting for commands for job {}".\
                                format(self.job_uuid))

                # we've handled message for 'this' job so exit loop (& thread)
                break
            else:
                logger.warning("self.job_uuid {}, command {} for alternate job_uuid {} ignored".\
                               format(self.job_uuid, command, job_uuid))

class PrimaryServer:
    """
    Class implementing the functions of the Primary component of the 
    Primary-Worker system

    Main entry point for submitting jobs and retrieving results
    """

    def __init__(self, primary_url, data_dir):
        self.primary_url = primary_url
        if(not os.path.exists(data_dir)):
            os.mkdir(data_dir)
        self.data_dir = data_dir

    def enqueue(self, job, job_data_blob=None, job_data_url=None):
        """
        Write job data to file and queue up for processing

        Note:  This should be run async wrt a web server as it will block
            on fetching/writing data

        Args:
            job_data_blob (blob):  blob of a zip file to be written to disk
            job_data_url (str):  the url of a zip file to fetched

        """

        # only allow job data as blob or url
        assert((job_data_blob is None) ^ (job_data_url is None))

        job_data_dir = os.path.join(self.data_dir, job.uuid)
        if(not os.path.exists(job_data_dir)):
            os.mkdir(job_data_dir)

        job_data_file = os.path.join(job_data_dir, "input.zip")
        if(job_data_blob):
            logger.info("writing input file for job to {}".\
                        format(job_data_file))
            file_handle = open(job_data_file, 'wb')
            file_handle.write(job_data_blob)
            file_handle.close()
        else:
            logger.info("retrieving input file for job and writing to {}".\
                        format(job_data_file))
            fetch_file_from_url(job_data_url, job_data_dir, "input.zip")

        # add to global job list then queue it to be run
        job.primary_url = self.primary_url
        job.primary_data_dir = self.data_dir  # to know where output.zip is
        job.status = Job.STATUS_QUEUED
        # save it
        Job[job.uuid] = job
        job_queue = "modelrunner:queues:{}".format(job.model)
        logger.info("adding job {} to queue {}".format(job.uuid, job_queue))
        settings.redis_connection().rpush(job_queue, job.uuid)

    def kill_job(self, job):
        """
        Notify Worker that a job should be killed

        Args:
            job (modelrunner.Job):  job instance
        """
        
        if job.status == Job.STATUS_QUEUED:
            # case 1:  job is in QUEUED state
            #          remove it from the queue and mark as killed
            job_queue = "modelrunner:queues:{}".format(job.model)
            logger.info("killing job {} by removing from queue {}".format(job.uuid, job_queue))
            settings.redis_connection().lrem(job_queue, 1, job.uuid)
            job.status = Job.STATUS_KILLED
            # save it
            Job[job.uuid] = job
        elif job.status == Job.STATUS_RUNNING:
            # case 2:  job is in RUNNING state
            #          send message to worker to kill the job (worker will update its status)
            worker_queue = "modelrunner:queues:{}:{}".format(job.worker_url, job.model)
            logger.info("sending message to kill job on worker {}:{}".\
                        format(job.worker_url, job.model))
            message = {'command': "KILL", 'job_uuid': job.uuid}
            settings.redis_connection().rpush(worker_queue, pickle.dumps(message))
        else:
            logger.info("kill called on job {} in incompatible state {}".\
                        format(job.uuid, job.status))

    def wait_for_finished_jobs(self):
        """
        Listen for jobs that have finished (by workers)

        This is meant to be called in an infinite loop in the primary server
        It blocks while waiting for finished jobs
        """
        primary_queue = "modelrunner:queues:" + self.primary_url
        logger.info("waiting for finished jobs on queue {}".\
                    format(primary_queue))
        result = settings.redis_connection().blpop(primary_queue)
        uuid = result[1]
        job = Job[uuid]

        logger.info("job {} finished with status of {}".format(job.uuid, 
                                                               job.status))
        # Get the job log from the worker
        logger.info("retrieving log for job {}".format(job.uuid))
        job_data_dir = os.path.join(self.data_dir, job.uuid)
        if(not os.path.exists(job_data_dir)):
            os.mkdir(job_data_dir)

        fetch_file_from_url(job.log_url(), job_data_dir)

        # Now get the job output data from the worker
        if(job.status == Job.STATUS_PROCESSED):

            logger.info("retrieving output for job {}".format(job.uuid))
            fetch_file_from_url(job.download_url(), job_data_dir)
            job.status = Job.STATUS_COMPLETE

        job.on_primary = True
        # save job
        Job[job.uuid] = job


class WorkerServer:
    """
    Class implementing the functions of the Worker component of the 
    Primary-Worker system

    Retrieves jobs from Primary, runs them and makes results available to 
    Primary with a notification

    Attributes:

        primary_url (str):  url of Primary server
        worker_url (str):  url of Worker server
        data_dir (str):  path where job data should be stored
        model_commands (dict str -> str):  model -> command to run model via

    """
    def __init__(
            self,
            primary_url,
            worker_url,
            data_dir,
            model_commands):

        self.primary_url = primary_url
        self.worker_url = worker_url
        self.model_commands = model_commands
        if(not os.path.exists(data_dir)):
            os.mkdir(data_dir)
        self.data_dir = data_dir

    def wait_for_new_jobs(self, model_name):
        """
        Listen for jobs to run as they come in on the model based queue

        This is meant to be called in an infinite loop as part of a worker.
        It blocks on waiting for job and while command is being run

        Args:
            model_name (str):  name of model this worker will run

        TODO:  
            - handle subprocess exceptions?
            - close job_log on exceptions?

        """
        job_queue = "modelrunner:queues:{}".format(model_name)
        logger.info("waiting for job on queue {}".format(job_queue))
        result = settings.redis_connection().blpop(job_queue)
        uuid = result[1]
        try:
            job = Job[uuid]
        except KeyError as e:
            # Job not found is not worth re-raising
            logger.warn(e)
            logger.warn("Jobs were removed without removing "
                        "corresponding queue entry")
            return

        # assign the job to this worker
        job.worker_url = self.worker_url
        # keep the worker_data_dir separate from primary
        job.worker_data_dir = self.data_dir
        # primary_queue to notify primary server of any errors or completion
        primary_queue = "modelrunner:queues:{}".format(self.primary_url)

        job_data_dir = os.path.join(self.data_dir, job.uuid)
        input_dir = os.path.join(job_data_dir, "input")
        output_dir = os.path.join(job_data_dir, "output")
        # create job data dirs if they don't exist
        if(not os.path.exists(input_dir)):
            os.makedirs(input_dir)

        if(not os.path.exists(output_dir)):
            os.makedirs(output_dir)

        # setup subproc to run model command and output to local job log
        # AND the associated 'kill thread'
        logger.info("preparing input for job {}".format(job.uuid))
        job_data_log = open(os.path.join(job_data_dir, "job_log.txt"), 'w')

        # catch data prep exceptions so that we mark the job as failed
        try:
            self._prep_input(job)
        except:
            # Fail the job, log it, notify primary and re-raise for caller
            failure_msg = "Failed prepping data for job {}".format(job.uuid)
            logger.error(failure_msg)
            job_data_log.write(failure_msg)
            job_data_log.close()
            job.status = Job.STATUS_FAILED
            # save job 
            Job[job.uuid] = job
            settings.redis_connection().rpush(primary_queue, job.uuid)
            raise

        # Input has been prepped so start the job
        command = self.model_commands[model_name]
        logger.info("starting job {}".format(job.uuid))

        # update job status
        job.status = Job.STATUS_RUNNING
        job.on_primary = False # now on worker
        Job[job.uuid] = job

        # add the input and output dir to the command
        command_args = command.split()
        input_dir = os.path.join(self.data_dir, job.uuid, "input")
        output_dir = os.path.join(self.data_dir, job.uuid, "output")
        command_args.append(os.path.realpath(input_dir))
        command_args.append(os.path.realpath(output_dir))
        command_str = subprocess.list2cmdline(command_args)
        logger.info("running command {}".format(command_str))
        popen_proc = subprocess.Popen(
                        command_args,
                        shell=False,
                        stdout=job_data_log,
                        stderr=job_data_log)

        logger.info("job {} running with pid {}".format(job.uuid, popen_proc.pid))
        worker_queue = "modelrunner:queues:{}:{}".format(self.worker_url, 
                                                         model_name)
        wait = WaitForCommand(worker_queue, popen_proc, job.uuid)
        wait.start()

        # wait for command to finish or for it to be killed
        return_code = popen_proc.wait()
        # close job log
        job_data_log.close()
        logger.info("finished job {} with return code {}".format(job.uuid, 
                                                                 return_code))
                                                                 
        # * This handles a race condition between parent being notified of
        # * killed sub-process and the WaitForCommand thread being cleaned up.
        # * Without this, it's possible for extra "BREAK" command to be sent
        # * (potentially cutting next job short)
        if (not wait.killed) and wait.isAlive():
            # send a message to stop the wait for kill thread
            message = {'command': "BREAK", 'job_uuid': job.uuid}
            settings.redis_connection().rpush(worker_queue, pickle.dumps(message))

        logger.info("finished processing job, notifying primary server {}".\
                    format(self.primary_url))

        # update job status (use command return code for now)
        if(return_code == 0):
            logger.info("zipping output of job {}".format(job.uuid))
            self._prep_output(job)
            job.status = Job.STATUS_PROCESSED
        else:
            if wait.killed:
                job.status = Job.STATUS_KILLED
            else:
                job.status = Job.STATUS_FAILED

        # save job
        Job[job.uuid] = job

        # notify primary server job is done
        settings.redis_connection().rpush(primary_queue, job.uuid)

    def _prep_input(self, job):
        """ fetch (if needed) and unzip data to appropriate dir """

        job_data_dir = os.path.join(self.data_dir, job.uuid)
        input_dir = os.path.join(job_data_dir, "input")

        input_zip = os.path.join(job_data_dir, "input.zip")

        # get the input
        input_url = job.primary_url + "/" +\
                    job.primary_data_dir + "/" +\
                    job.uuid + "/input.zip"

        logger.info("fetching data from {}".format(input_url))
        fetch_file_from_url(input_url, job_data_dir)

        # unzip the input file
        with ZipFile(input_zip, 'r') as zip_file:
            zip_file.extractall(input_dir)

    def _prep_output(self, job):
        """ zip files in the output dir """

        job_data_dir = os.path.join(self.data_dir, job.uuid)
        output_zip_name = os.path.join(job_data_dir, "output.zip")

        output_dir = os.path.join(job_data_dir, "output")
        zipdir(output_dir, output_zip_name)

