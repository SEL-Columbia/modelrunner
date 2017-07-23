# -*- coding: utf-8 -*-
"""
Main modelrunner package
"""

# initialize logging
import logging
from .job import Job  # noqa
from .node import Node  # noqa
from .dispatcher import Dispatcher  # noqa
from .worker_server import WorkerServer  # noqa
from .primary_server import PrimaryServer  # noqa

__version__ = "0.7.2"

logger = logging.getLogger('modelrunner')
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')

ch.setFormatter(formatter)
logger.addHandler(ch)

# need to set this, otherwise 'root' logger also logs
logging.getLogger('modelrunner').propagate = False
