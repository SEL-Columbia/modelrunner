# -*- coding: utf-8 -*-
"""
Job
"""

import datetime
from uuid import uuid4
from redisent import RedisEntity


class Job(RedisEntity):
    """
    Maintain the state of a ModelRunner Job

    Attributes:
        model (str):  name of model job should run
        name (str):  name of job
        uuid (str):  unique uuid4 string id'ing job
        created (datetime|str):  time created
            if its a string, should be in iso format and will be
            cast to datetime
        status (str):  One of STATUS constants
        primary_url (str):  The URL of the primary server for the job
        worker_url (str):  URL of the worker server for the job
        primary_data_dir (str):  path on primary server holding job data
        worker_data_dir (str):  path on worker server holding job data
        on_primary (bool): whether job is currently on primary or worker

    """

    STATUS_CREATED = "CREATED"
    STATUS_QUEUED = "QUEUED"
    STATUS_RUNNING = "RUNNING"
    STATUS_PROCESSED = "PROCESSED"
    STATUS_COMPLETE = "COMPLETE"
    STATUS_FAILED = "FAILED"
    STATUS_KILLED = "KILLED"

    def __init__(self,
                 model=None,
                 name=None,
                 uuid=None,
                 created=None,
                 status=STATUS_CREATED,
                 primary_url=None,
                 worker_url=None,
                 primary_data_dir=None,
                 worker_data_dir=None,
                 on_primary=True):

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
        self.on_primary = on_primary

    def get_data_dir(self):
        """
        Get the data directory name configured for this job

        Returns:
            the data dir for this job on worker or primary (default is "data")
        """
        if(not self.on_primary):
            if(getattr(self, "worker_data_dir", False)):
                return self.worker_data_dir
        else:
            if(getattr(self, "primary_data_dir", False)):
                return self.primary_data_dir

        return "data"

    def get_url(self):
        """ url based on on_primary attribute """
        server_url = self.primary_url if self.on_primary else self.worker_url
        return server_url

    def log_url(self):
        """
        Get current url of the jobs log
        NOTE:  This will change depending on whether job is on_primary
        """

        url = "{}/{}/{}/job_log.txt".format(
            self.get_url(),
            self.get_data_dir(),
            self.uuid)

        return url

    def download_url(self):
        url = "{}/{}/{}/output.zip".format(
            self.get_url(),
            self.get_data_dir(),
            self.uuid)

        return url
