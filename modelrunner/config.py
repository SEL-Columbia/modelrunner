# -*- coding: utf-8 -*-
"""
Define the config parameters

Use tornado.options as it seems pretty friendly

These can be overridden via parse_config_file and parse_command_line
"""

import os
from tornado.options import define, options

define("config_file", default="config.ini", help="config file for modelrunner")
define("port", default=8888, help="run on the given port", type=int)
define("debug", default=False, help="run in debug mode")
define("redis_url", default="localhost:6379", help="Redis server connection")
define(
    "primary_url",
    default="localhost:8000",
    help="Primary job data server url")
define(
    "worker_url",
    default="localhost:8000",
    help="Local job data server url")
define("data_dir", default="data", help="Local job data directory")
define(
    "input_file",
    default="input.zip",
    help="input file for new job (job_creator only)")
define("model", default="test", help="model to be run")
define(
    "worker_is_primary",
    default=True,
    help="Whether worker and primary are one")
define(
    "admin_key",
    default="",
    help="key to access admin site")
define(
    "template_path",
    default=os.path.join(os.path.curdir, "templates"),
    help="directory where html template files reside")
define(
    "static_path",
    default=os.path.join(os.path.curdir, "static"),
    help="directory where static web files reside")
define(
    "sequencer",
    default="./sequencer.sh",
    help="sequence model command",
    group="model_command")
define(
    "networkplanner",
    default="./networkplanner.sh",
    help="networkplanner model command",
    group="model_command")
define(
    "networker",
    default="./networker.sh",
    help="networker model command",
    group="model_command")
define(
    "test",
    default="./test.sh",
    help="test model command",
    group="model_command")
