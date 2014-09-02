import tornado
import tornado.ioloop
import tornado.web
import os, uuid

# setup config options
import config

from tornado.options import parse_command_line, parse_config_file

import job_manager
import subprocess

__JOB_DIR__ = "data/"

if __name__ == "__main__":
    parse_command_line()
    parse_config_file("config.ini")
    # get the command_ keys
    command_keys = [key for key in config.options.as_dict().keys() if key.startswith("model_command")]
    comand_dict = {k: config.options.as_dict().get(k, None) for k in command_keys}
    # TODO:  Setup JobManager with config options and command_dict

    result = subprocess.Popen("./test.sh".split(), shell=True)
