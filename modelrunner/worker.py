# -*- coding: utf-8 -*-
"""
Worker
"""

import datetime
from redisent import RedisEntity

class Worker(RedisEntity):
    """
    Represent the state of a ModelRunner Worker

    Attributes:
        name (str):  name of worker
        model (str):  name of model that worker runs
        status (str):  One of STATUS constants
        job_uuid (str):  uuid of running job
        job_pid (int):  process id of process running job
    """

    STATUS_WAITING   = "WAITING"
    STATUS_RUNNING   = "RUNNING"

    def __init__(self, 
                 name=None,
                 model=None,
                 status=STATUS_WAITING,
                 job_uuid=None,
                 job_pid=None):

        self.name = name
        self.model = model
        self.status = status
        self.job_uuid = job_uuid
        self.job_pid = job_pid
