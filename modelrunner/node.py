# -*- coding: utf-8 -*-
import datetime
from redisent import RedisEntity

class Node(RedisEntity):
    """
    Represent the state of a Node that participates in the 
    ModelRunner 'protocol'

    Attributes:
        name (str): name of worker
        node_url (str): url where node resides 
        status (str): one of STATUS constants
        node_type (str): one of TYPE constants
        version (str): version of modelrunner 
        # only pertain to WORKER nodes
        model (str): name of model that worker runs
    """

    TYPE_PRIMARY = "PRIMARY"
    TYPE_WORKER  = "WORKER"

    STATUS_WAITING   = "WAITING"
    STATUS_RUNNING   = "RUNNING"

    def __init__(self, 
                 name=None,
                 node_url=None,
                 status=STATUS_WAITING,
                 node_type=None,
                 version=None,
                 model=None):

        self.name = name
        self.node_url = node_url
        self.status = status
        self.node_type = node_type
        self.version = version
        self.model = model

    def __str__(self):
        return str(self.__dict__)
