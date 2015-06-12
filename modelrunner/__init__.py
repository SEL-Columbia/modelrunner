# -*- coding: utf-8 -*-
"""
Main modelrunner package
"""

# initialize logging
import logging

__version__ = "0.3.0"

logger = logging.getLogger('modelrunner')
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')

ch.setFormatter(formatter)
logger.addHandler(ch)

# need to set this, otherwise 'root' logger also logs
logging.getLogger('modelrunner').propagate = False

from manager import JobManager
from manager import Job
