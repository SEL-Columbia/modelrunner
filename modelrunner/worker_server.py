# -*- coding: utf-8 -*-

import os
import logging
import subprocess
import signal
from zipfile import ZipFile
import modelrunner
from modelrunner.utils import fetch_file_from_url, zipdir, kill_process_tree
from modelrunner.redis_utils import enqueue_command
from modelrunner.settings import redis_connection,\
                                 primary_queue_name,\
                                 worker_name

from . import Job
from . import Node

logger = logging.getLogger('modelrunner')

class WorkerServer:
    """
    Class implementing the functions of the Worker component of the
    Primary-Worker system

    Implements 'CommandHandler interface' required by JobNode

    Retrieves jobs from queue, runs them and makes results available to
    Primary via it's queue

    Attributes:

        worker_url (str):  url of Worker server
        data_dir (str):  path where job data should be stored
        model (str):  name of model to be run via this worker
        model_commands (dict str -> str):  model -> command to run model via

    """
    def __init__(
            self,
            worker_url,
            data_dir,
            model,
            model_commands):

        self.model_commands = model_commands
        if(not os.path.exists(data_dir)):
            os.mkdir(data_dir)
        self.data_dir = data_dir

        # used for reporting status
        self._node = Node(
                        worker_name(worker_url, model),
                        worker_url,
                        Node.STATUS_WAITING,
                        Node.TYPE_WORKER,
                        modelrunner.__version__,
                        model)

        self.dispatch = {
            'PROCESS_JOB': self.process_job,
            'KILL_JOB': self.kill_job,
            'UPDATE_STATUS':  self.update_status,
        }

    @property
    def node(self):
        """
        We don't want others manipulating the node directly
        """
        return self._node

    def process_job(self, command_dict):
        """
        process job
        command format {'command': 'PROCESS_JOB',
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

        # assign the job to this worker
        job.worker_url = self.node.node_url
        job.worker_data_dir = self.data_dir
        job_data_dir = self._setup_job_dir(job)

        # setup subproc to run model command and output to local job log
        logger.info("preparing input for job {}".format(job.uuid))
        job_data_log = open(os.path.join(job_data_dir, "job_log.txt"), 'w')

        # primary_queue to notify primary server of any errors or completion
        primary_queue = primary_queue_name(job.primary_url)

        # catch data prep exceptions so that we mark the job as failed
        try:
            self._prep_input(job)
        except:
            # Fail the job, log it and notify primary
            failure_msg = "Failed prepping data for job {}".format(job.uuid)
            logger.error(failure_msg)
            job_data_log.write(failure_msg)
            job_data_log.close()
            job.status = Job.STATUS_FAILED
            Job[job.uuid] = job
            command_dict = {'command': 'COMPLETE', 'job_uuid': job.uuid}
            enqueue_command(redis_connection(), primary_queue, command_dict)
            return

        # Input has been prepped so start the job
        command = self.model_commands[self.node.model]
        logger.info("starting job {}".format(job.uuid))

        # update job status
        job.status = Job.STATUS_RUNNING
        job.on_primary = False # now on worker
        Job[job.uuid] = job

        # add the input and output dir to the command
        popen_proc = self._run_subprocess(command, job, job_data_log)

        # set hidden status attributes
        self._update_worker_status(Node.STATUS_RUNNING,
                                   job_uuid=job.uuid,
                                   job_pid=popen_proc.pid)

        logger.info("job {} running with pid {}".format(job.uuid, popen_proc.pid))

        # wait for command to finish or for it to be killed
        return_code = popen_proc.wait()

        # Reset hidden status attributes
        self._update_worker_status(Node.STATUS_WAITING)

        # close job log
        job_data_log.close()
        logger.info("finished job {} with return code {}".format(job.uuid,
                                                                 return_code))

        # update job status (use command return code for now)
        if(return_code == 0):
            logger.info("zipping output of job {}".format(job.uuid))
            self._prep_output(job)
            job.status = Job.STATUS_PROCESSED
        elif return_code == -signal.SIGKILL:
            job.status = Job.STATUS_KILLED
        else:
            job.status = Job.STATUS_FAILED

        Job[job.uuid] = job

        # notify primary server job is done
        command_dict = {'command': 'COMPLETE_JOB', 'job_uuid': job.uuid}
        enqueue_command(redis_connection(), primary_queue, command_dict)

    def kill_job(self, command_dict):
        """
        handle command to kill running job on this worker

        command format {'command': 'KILL_JOB',
                        'job_uuid': <uuid>}
        """
        # ensure the command makes sense
        if self.node.status == Node.STATUS_RUNNING and \
           self._job_uuid == command_dict['job_uuid']:
            try:
                kill_process_tree(self._job_pid)
            except Exception as e:
                logger.warning(
                    "exception occurred while killing pid {}: {}".\
                    format(self._job_pid, e))
        else:
            logger.warning("command {} ignored".format(command_dict))

    def update_status(self, command_dict):
        """
        handle command to update global status of this node

        command format {'command': 'UPDATE_STATUS'}
        """
        # just save it as Node redis entity
        Node[self.node.name] = self.node

    def _update_worker_status(self, status, job_uuid=None, job_pid=None):
        # set hidden worker attributes
        self._node.status = status
        self._job_uuid = job_uuid
        self._job_pid = job_pid

    def _setup_job_dir(self, job):
        """
        setup parent job dir, and input/output subdirs
        return parent job dir
        """
        job_data_dir = os.path.join(self.data_dir, job.uuid)
        input_dir = os.path.join(job_data_dir, "input")
        output_dir = os.path.join(job_data_dir, "output")
        # create job data dirs if they don't exist
        if(not os.path.exists(input_dir)):
            os.makedirs(input_dir)

        if(not os.path.exists(output_dir)):
            os.makedirs(output_dir)
        return job_data_dir

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

    def _run_subprocess(self, command, job, job_data_log):
        """ run command in a subproc and return the popen_proc """
        command_args = command.split()
        input_dir = os.path.join(self.data_dir, job.uuid, "input")
        output_dir = os.path.join(self.data_dir, job.uuid, "output")
        command_args.append(os.path.realpath(input_dir))
        command_args.append(os.path.realpath(output_dir))
        command_str = subprocess.list2cmdline(command_args)
        logger.info("running command {}".format(command_str))
        return subprocess.Popen(
                        command_args,
                        shell=False,
                        stdout=job_data_log,
                        stderr=job_data_log)
