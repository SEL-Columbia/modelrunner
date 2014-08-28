"""
Define the config parameters

Use tornado.options as it seems pretty friendly

These can be overridden via parse_config_file and parse_command_line
"""

from tornado.options import define, options

define("port", default=8888, help="run on the given port", type=int)
define("debug", default=False, help="run in debug mode")
define("redis_url", default="localhost:6379", help="Redis server connection")
define("primary_url", default="localhost:8888", help="Primary job api server connection")
define("worker_url", default="localhost:8000", help="Local job data server url")
define("data_dir", default="data", help="Local job data directory")


