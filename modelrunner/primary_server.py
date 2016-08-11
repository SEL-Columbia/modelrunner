# -*- coding: utf-8 -*-

import os
import logging

import modelrunner
from modelrunner.utils import fetch_file_from_url
from modelrunner.redis_utils import enqueue_command,\
                                    remove_command,\
                                    publish_command

from modelrunner.settings import redis_connection,\
                                 job_queue_name,\
                                 worker_name,\
                                 primary_queue_name,\
                                 node_channel_name

from . import Job
from . import Node

logger = logging.getLogger('modelrunner')

class PrimaryServer:
    """
    Class implementing the functions of the Primary component of the 
    Primary-Worker system

    Implements 'CommandHandler interface' required by TaskNode

    Main entry point for submitting jobs and retrieving results
    """

    def __init__(self, primary_url, data_dir):
        if(not os.path.exists(data_dir)):
            os.mkdir(data_dir)
        self.data_dir = data_dir

        self.dispatch = {
            'COMPLETE_JOB': self.complete_job,
            'UPDATE_STATUS':  self.update_status
        }

        # used for reporting status
        self._node = Node(primary_url,
                          primary_url,
                          Node.STATUS_WAITING,
                          Node.TYPE_PRIMARY,
                          modelrunner.__version__)

    @property
    def node(self):
        """
        We don't want others manipulating the node directly
        """
        return self._node


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
        job.primary_url = self.node.node_url
        job.primary_data_dir = self.data_dir  # to know where output.zip is
        job.status = Job.STATUS_QUEUED
        Job[job.uuid] = job
        job_queue = job_queue_name(job.model)
        command_dict = {'command': 'PROCESS_JOB', 'job_uuid': job.uuid}
        enqueue_command(redis_connection(), job_queue, command_dict)

    def kill_job(self, job):
        """
        Notify Worker that a job should be killed

        Args:
            job (modelrunner.Job):  job instance
        """
        
        if job.status == Job.STATUS_QUEUED:
            # case 1:  job is in QUEUED state
            #          remove it from the queue and mark as killed

            job_queue = job_queue_name(job.model)
            logger.info("killing job {} by removing from queue {}".format(job.uuid, job_queue))
            command_dict = {'command': 'PROCESS_JOB', 'job_uuid': job.uuid}
            remove_command(redis_connection(), job_queue, command_dict)
            job.status = Job.STATUS_KILLED
            # save it
            Job[job.uuid] = job
        elif job.status == Job.STATUS_RUNNING:
            # case 2:  job is in RUNNING state
            #          send message to worker to kill the job (worker will update its status)
            worker = worker_name(job.worker_url, job.model)
            worker_channel = node_channel_name(worker)
            logger.info("sending command to kill job on channel {}".\
                        format(worker_channel))
            command_dict = {'command': "KILL_JOB", 'job_uuid': job.uuid}
            publish_command(redis_connection(), worker_channel, command_dict)
        else:
            logger.info("kill called on job {} in incompatible state {}".\
                        format(job.uuid, job.status))

    def complete_job(self, command_dict):
        """
        Handle jobs that have been completed (by workers)

        command format {'command': 'COMPLETE_JOB',
                        'job_uuid': <uuid>}

        """
        job_uuid = command_dict['job_uuid']
        try:
            job = Job[job_uuid]
        except KeyError as e:
            # Job not found is not worth re-raising
            logger.warn(e)
            logger.warn("Job {} missing".format(job_uuid))
            return

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

    def update_status(self, command_dict):
        """
        handle command to update global status of this node

        command format {'command': 'UPDATE_STATUS'}
        """
        # just save it as Node redis entity
        Node[self.node.name] = self.node
