#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Web Server

Script to handle web interactions via tornado

See config.py or pass --help to command for command line args
"""

import sys
import logging

import modelrunner
from modelrunner.settings import initialize
from modelrunner import config
from modelrunner import server
from tornado.options import parse_command_line, parse_config_file

import tornado
import tornado.ioloop
import tornado.web
import tornado.escape
import tornado.gen


# setup log
logger = logging.getLogger('modelrunner')

logger.info("modelrunner %s (Python %s)" %
            (modelrunner.__version__,
             '.'.join(map(str, sys.version_info[:3]))))

# so we can load config via cmd line args
parse_command_line()
parse_config_file(config.options.config_file)

# initialize the global application settings
initialize(config.options.redis_url)

# get the command keys
command_dict = config.options.group_dict("model_command")
models = command_dict.keys()

primary_server = modelrunner.PrimaryServer(config.options.primary_url,
                                           config.options.data_dir)

app_settings = {
    "static_path": config.options.static_path,
}

job_id_regex = "([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})"
application = tornado.web.Application([
        (r"/", server.MainHandler),
        (r"/jobs/submit", server.SubmitJobForm, dict(models=models)),
        (r"/jobs", server.JobHandler, dict(primary_server=primary_server)),
        (r"/jobs/{}".format(job_id_regex),
            server.JobHandler, dict(primary_server=primary_server)),
        (r"/jobs/{}/kill".format(job_id_regex),
            server.JobKillHandler, dict(primary_server=primary_server)),
        (r"/status", server.StatusHandler, dict(primary_server=primary_server)),
        (r"/admin/(.*)",
         server.AdminHandler,
         dict(primary_server=primary_server,
              admin_key=config.options.admin_key))
        ],
        template_path=config.options.template_path,
        debug=config.options.debug,
        ui_modules={'JobOptions': server.JobOptionsModule},
        **app_settings
        )

logger.info("modelrunner server listening on port %s" % config.options.port)
application.listen(config.options.port)

tornado.ioloop.IOLoop.instance().start()
