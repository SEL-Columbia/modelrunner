#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Web Server

Script to handle web interactions via tornado

See config.py or pass --help to command for command line args
"""

import os
import sys
import logging
from modelrunner import config
from tornado.options import parse_command_line, parse_config_file

import tornado
import tornado.ioloop
import tornado.web
import tornado.escape
import tornado.gen

import modelrunner as mr
import modelrunner.server as server

# setup log
logger = logging.getLogger('modelrunner')

logger.info("modelrunner %s (Python %s)" %
            (mr.__version__,
             '.'.join(map(str, sys.version_info[:3]))))

# so we can load config via cmd line args
parse_command_line()
parse_config_file(config.options.config_file)

# get the command_ keys
command_dict = config.options.group_dict("model_command")
models = command_dict.keys()

jm = mr.JobManager(config.options.redis_url,
                   config.options.primary_url,
                   config.options.worker_url,
                   config.options.data_dir,
                   command_dict,
                   config.options.worker_is_primary)

settings = {
    "static_path": os.path.join(os.path.dirname(__file__), "static"),
}

application = tornado.web.Application([
        (r"/", server.MainHandler),
        (r"/jobs/submit", server.SubmitJobForm, dict(models=models)),
        (r"/jobs", server.JobHandler, dict(job_mgr=jm)),
        (r"/jobs/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})",
            server.JobHandler, dict(job_mgr=jm)),
        (r"/jobs/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})/kill",
            server.JobKillHandler, dict(job_mgr=jm)),
        ],
        template_path=os.path.join(os.path.dirname(__file__), "templates"),
        debug=config.options.debug,
        ui_modules={'JobOptions': server.JobOptionsModule},
        **settings
        )

application.listen(config.options.port)

# TODO:  Setup JobManager with config options and command_dict
tornado.ioloop.IOLoop.instance().start()
