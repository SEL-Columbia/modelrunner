# -*- coding: utf-8 -*-
"""
Module for managing job running and sync between primary and workers
"""

import os
from uuid import uuid4
import datetime
import json
import redis
import re
import pickle
import logging
import urllib2
import threading
import subprocess
import zipfile
from zipfile import ZipFile

# setup log
logger = logging.getLogger('modelrunner')


def fetch_file_from_url(url, destination_dir, file_name=None):
    """
    Utility function for retrieving a remote file from a url

    Args:
        url (str):  http based url for file to retrieve
        destination_dir (str):  local dir to place file in
        file_name (str):  name of local copy of file (if None glean from url)
    """

    # http://stackoverflow.com/questions/22676/how-do-i-download-a-file-over-http-using-python
    if(not file_name):
        file_name = url.split('/')[-1]

    u = urllib2.urlopen(url)
    destination_file = os.path.join(destination_dir, file_name)
    f = open(destination_file, 'wb')
    logger.info("Downloading from url {}".format(url))

    file_size_dl = 0
    block_sz = 8192
    while True:
        buffer = u.read(block_sz)
        if not buffer:
            break

        file_size_dl += len(buffer)
        f.write(buffer)

    logger.info("Finished %s bytes from url %s" % (file_size_dl, url))
    f.close()


def zipdir(path, zip_file_name):
    """
    Recursively zip up a directory

    Args:
        path (str):  local path of dir to be zipped
        zip_file_name (str):  name of zip to be created
    """

    output_zip = ZipFile(zip_file_name, 'w')
    for root, dirs, files in os.walk(path):
        for file in files:
            rel_path = os.path.relpath(os.path.join(root, file), path)
            output_zip.write(
                os.path.join(root, file),
                arcname=rel_path,
                compress_type=zipfile.ZIP_DEFLATED)

    output_zip.close()


class WaitForKill(threading.Thread):
    """
    Thread used by JobManager to wait for kills while process is running

    Attributes:
        redis_obj (redis.Redis):  Redis connection instance
        worker_queue (str):  name of worker queue to listen for commands
        popen_proc (subprocess):  subprocess running job to be managed
        job_uuid (str):  uuid of job managed by this thread

    """

    def __init__(self, redis_obj, worker_queue, popen_proc, job_uuid):
        threading.Thread.__init__(self)
        self.redis_obj = redis_obj
        self.worker_queue = worker_queue
        self.popen_proc = popen_proc
        self.job_uuid = job_uuid

    def run(self):
        """
        Wait for commands associated with this job

        handle case where kill message for "old" job is submitted
        by pulling off messages until one associated with 'this' job is found
        (otherwise, we might kill new jobs via messages for old jobs)

        When job is completed, a BREAK message should be sent to
        stop this thread.
        """
        while(True):
            # block on queue and unpickle message dict when it arrives
            raw_message = self.redis_obj.blpop(self.worker_queue)[1]
            message = pickle.loads(raw_message)
            job_uuid = message['job_uuid']
            command = message['command']
            logger.info("Received command {} for job_uuid {} on queue {}".
                        format(command, job_uuid, self.worker_queue))

            if(job_uuid == self.job_uuid):
                if(command == "KILL"):
                    logger.info("Terminating pid {}".
                                format(self.popen_proc.pid))
                    self.popen_proc.terminate()

                if(command == "BREAK"):
                    logger.info("Stop waiting for commands for job {}".
                                format(self.job_uuid))

                # we've handled message for 'this' job so exit loop (& thread)
                break
            else:
                logger.info("Command {} for OLD job_uuid {} ignored".
                            format(command, job_uuid))


class JobManager:

    """
    Class to manage running jobs and synchronizing associated data between
    *Primary* and *Worker* servers

    Primary server:  Main entry point for submitting jobs and for worker sync
    Worker server:  Retrieves jobs from Primary, runs them and makes results
        available to Primary with a notification

    Attributes:
        rdb (redis.Redis):  Redis DB connection
        primary_url (str):  url of Primary server
        worker_url (str):  url of Worker server
        model_commands (dict str -> str):  model -> command to run model via
        data_dir (str):  path where job data should be stored

    """

    # Job Statuses
    STATUS_CREATED   = "CREATED"
    STATUS_QUEUED    = "QUEUED"
    STATUS_RUNNING   = "RUNNING"
    STATUS_PROCESSED = "PROCESSED"
    STATUS_COMPLETE  = "COMPLETE"
    STATUS_FAILED    = "FAILED"

    def __init__(
            self,
            redis_url,
            primary_url,
            worker_url,
            data_dir,
            model_commands,
            worker_is_primary=True):

        port_re = re.compile(r'(?<=:)\d+$')
        host_re = re.compile(r'^.*(?=:\d+$)')
        redis_host_match = host_re.search(redis_url)
        redis_port_match = port_re.search(redis_url)
        if(not redis_host_match or not redis_port_match):
            raise ValueError("invalid redis url: %s" % redis_url)

        self.rdb = redis.Redis(host=redis_host_match.group(0),
                               port=redis_port_match.group(0))
        self.primary_url = primary_url
        self.worker_url = worker_url
        self.model_commands = model_commands
        self._worker_is_primary = worker_is_primary
        if(not os.path.exists(data_dir)):
            os.mkdir(data_dir)
        self.data_dir = data_dir

    # <wrappers> (for storing/retrieveing jobs in Redis)
    def hset(self, hash_name, key, job):
        json_job = json.dumps(job, cls=JobEncoder)
        self.rdb.hset(hash_name, key, json_job)

    def hget(self, hash_name, key):
        json_job = self.rdb.hget(hash_name, key)
        return json.loads(json_job, object_hook=decode_job)

    def hgetall(self, hash_name):
        json_jobs = self.rdb.hgetall(hash_name)
        return [json.loads(json_job[1], object_hook=decode_job) 
                for json_job in json_jobs.items()]
    # </wrappers>

    def get_jobs(self):
        """
        Get all jobs from Redis
        """
        return self.hgetall("modelrunner:jobs")

    def get_job(self, job_uuid):
        """
        Get specific job

        Args:
            job_uuid (str):  job id
        """
        return self.hget("modelrunner:jobs", job_uuid)

    def add_update_job_table(self, job):
        """
        Add or update a job in Redis

        Args:
            job (modelrunner.Job):  job instance
        """
        self.hset("modelrunner:jobs", job.uuid, job)

    def enqueue(self, job, job_data_blob=None, job_data_url=None):
        """
        Write job data to file and queue up for processing

        Run by Primary server

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
            logger.info("writing input file for job to {}".
                        format(job_data_file))
            file_handle = open(job_data_file, 'wb')
            file_handle.write(job_data_blob)
            file_handle.close()
        else:
            logger.info("retrieving input file for job and writing to {}".
                        format(job_data_file))
            fetch_file_from_url(job_data_url, job_data_dir, "input.zip")

        # add to global job list then queue it to be run
        job.primary_url = self.primary_url
        job.primary_data_dir = self.data_dir  # to know where output.zip is
        self.add_update_job_table(job)
        job_queue = "modelrunner:queues:%s" % job.model

        logger.info("adding job %s to queue %s" % (job.uuid, job_queue))
        self.rdb.rpush(job_queue, job.uuid)

    def wait_for_new_jobs(self, model_name):
        """
        Listen for jobs to run as they come in on the model based queue

        Run by Worker

        This is meant to be called in an infinite loop as part of a worker.
        It blocks on waiting for job and while command is being run

        Args:
            model_name (str):  name of model this worker will run

        """
        job_queue = "modelrunner:queues:%s" % model_name
        logger.info("waiting for job on queue %s" % job_queue)
        result = self.rdb.blpop(job_queue)
        uuid = result[1]
        job = self.get_job(uuid)

        # assign the job to this worker
        job.worker_url = self.worker_url
        # keep the worker_data_dir separate from primary
        job.worker_data_dir = self.data_dir
        # primary_queue to notify primary server of any errors or completion
        primary_queue = "modelrunner:queues:" + self.primary_url

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
        logger.info("preparing input for job %s" % job.uuid)
        job_data_log = open(os.path.join(job_data_dir, "job_log.txt"), 'w')

        # catch data prep exceptions so that if the job fails, we don't
        # kill the worker
        try:
            self._prep_input(job)
        except Exception as e:
            # Fail the job, log it, notify primary and get outta here
            failure_msg = "Failed prepping data: %s" % e
            logger.info(failure_msg)
            job_data_log.write(failure_msg)
            job.status = JobManager.STATUS_FAILED
            self.add_update_job_table(job)
            self.rdb.rpush(primary_queue, job.uuid)
            job_data_log.close()
            return

        # Input has been prepped so start the job
        command = self.model_commands[model_name]
        logger.info("starting job %s" % job.uuid)
        # update job status
        job.status = JobManager.STATUS_RUNNING
        self.add_update_job_table(job)

        # add the input and output dir to the command
        command_args = command.split()
        input_dir = os.path.join(self.data_dir, job.uuid, "input")
        output_dir = os.path.join(self.data_dir, job.uuid, "output")
        command_args.append(os.path.realpath(input_dir))
        command_args.append(os.path.realpath(output_dir))
        command_str = subprocess.list2cmdline(command_args)
        logger.info("running command %s" % command_str)
        popen_proc = subprocess.Popen(
                        command_str,
                        shell=True,
                        stdout=job_data_log,
                        stderr=job_data_log)

        worker_queue = "modelrunner:queues:" + self.worker_url
        wk = WaitForKill(self.rdb, worker_queue, popen_proc, job.uuid)
        wk.start()

        # wait for command to finish or for it to be killed
        return_code = popen_proc.wait()
        # close job log
        job_data_log.close()
        logger.info("finished job {} with return code {}".
                    format(job.uuid, return_code))

        if (wk.isAlive()):
            # send a message to stop the wait for kill thread
            message = {'command': "BREAK", 'job_uuid': job.uuid}
            self.rdb.rpush(worker_queue, pickle.dumps(message))

        logger.info("finished processing job, notifying primary server {}".
                    format(self.primary_url))

        # update job status (use command return code for now)
        if(return_code == 0):
            logger.info("zipping output of job %s" % job.uuid)
            self._prep_output(job)
            job.status = JobManager.STATUS_PROCESSED
        else:
            job.status = JobManager.STATUS_FAILED

        self.add_update_job_table(job)

        # notify primary server job is done
        self.rdb.rpush(primary_queue, job.uuid)

    def wait_for_finished_jobs(self):
        """
        Listen for jobs that have finished (by workers)

        Run by Primary

        This is meant to be called in an infinite loop in the primary server
        It blocks while waiting for finished jobs
        """
        primary_queue = "modelrunner:queues:" + self.primary_url
        logger.info("waiting for finished jobs on queue %s" % primary_queue)
        result = self.rdb.blpop(primary_queue)
        uuid = result[1]
        job = self.get_job(uuid)

        logger.info("job {} finished with status of {}".
                    format(job.uuid, job.status))
        if(job.status == JobManager.STATUS_PROCESSED):
            if(not self.worker_is_primary()):  # need to get output
                logger.info("retrieving output for job {}".format(job.uuid))
                output_url = job.worker_url + "/" +\
                    job.worker_data_dir + "/" +\
                    job.uuid + "/output.zip"

                job_data_dir = os.path.join(self.data_dir, job.uuid)
                if(not os.path.exists(job_data_dir)):
                    os.mkdir(job_data_dir)

                fetch_file_from_url(output_url, job_data_dir)

            job.status = JobManager.STATUS_COMPLETE
            self.add_update_job_table(job)

    def kill_job(self, job):
        """
        Notify job worker that the job should be killed

        Run by Primary

        Args:
            job (modelrunner.Job):  job instance
        """
        worker_queue = "modelrunner:queues:" + job.worker_url
        logger.info("sending message to kill job on %s" % job.worker_url)
        message = {'command': "KILL", 'job_uuid': job.uuid}
        self.rdb.rpush(worker_queue, pickle.dumps(message))

    def _prep_input(self, job):
        """ fetch (if needed) and unzip data to appropriate dir """

        job_data_dir = os.path.join(self.data_dir, job.uuid)
        input_dir = os.path.join(job_data_dir, "input")

        input_zip = os.path.join(job_data_dir, "input.zip")
        if not self.worker_is_primary():
            # need to fetch
            input_url = job.primary_url + "/" +\
                        job.primary_data_dir + "/" +\
                        job.uuid + "/input.zip"

            logger.info("fetching data from {}".format(input_url))
            fetch_file_from_url(input_url, job_data_dir)

        # if we're here, we just need to unzip the input file
        with ZipFile(input_zip, 'r') as zip_file:
            zip_file.extractall(input_dir)

    def _prep_output(self, job):
        """ zip files in the output dir """

        job_data_dir = os.path.join(self.data_dir, job.uuid)
        output_zip_name = os.path.join(job_data_dir, "output.zip")

        output_dir = os.path.join(job_data_dir, "output")
        zipdir(output_dir, output_zip_name)

    def worker_is_primary(self):
        """
        Determine whether the machine this is running on is also primary
        """

        return self._worker_is_primary


class Job:
    """
    Maintain the state of a ModelRunner Job

    Attributes:
        model (str):  name of model job should run
        name (str):  name of job
        uuid (str):  unique uuid4 string id'ing job
        created (datetime|str):  time created
            if its a string, should be in iso format and will be
            cast to datetime
        status (str):  One of JobManager defined STATUS constants
        primary_url (str):  The URL of the primary server for the job
        worker_url (str):  URL of the worker server for the job
        primary_data_dir (str):  path on primary server holding job data
        worker_data_dir (str):  path on worker server holding job data

    """

    def __init__(self,
                 model=None,
                 name=None,
                 uuid=None,
                 created=None,
                 status=JobManager.STATUS_CREATED,
                 primary_url=None,
                 worker_url=None,
                 primary_data_dir=None,
                 worker_data_dir=None):

        self.model = model
        self.name = name
        self.uuid = uuid if uuid else str(uuid4())
        # allow created to be an iso formatted string
        # that we cast to datetime.datetime
        if isinstance(created, basestring):
            created = datetime.datetime.strptime(created,
                                                 "%Y-%m-%dT%H:%M:%S.%f")
        self.created = created if created else datetime.datetime.utcnow()
        self.status = status
        self.primary_url = primary_url
        self.worker_url = worker_url
        self.primary_data_dir = primary_data_dir
        self.worker_data_dir = worker_data_dir


class JobEncoder(json.JSONEncoder):
    """
    Encode Job as something that can be json serialized
    """
    def default(self, obj):
        if isinstance(obj, Job):
            return obj.__dict__
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        return json.JSONEncoder.default(self, obj)


def decode_job(dict):
    """
    Decode a job from a dict (useful for JSON decoding)
    """
    return Job(**dict)