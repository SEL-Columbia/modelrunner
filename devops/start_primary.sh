#!/bin/bash

# start all processes in support of primary server in background
# assumes model_runner conda environment has been activated
nohup redis-server > redis.log 2>&1 & echo $! > redis.pid 
nohup python job_server.py --port=8080 --worker_is_primary=False > job_server.log 2>&1 & echo $! > job_server.pid
nohup python -m SimpleHTTPServer 8000 > primary_static_server.log 2>&1 & echo $! > primary_static_server.pid
nohup python job_primary.py --worker_is_primary=False > job_primary.log 2>&1 & echo $! > job_primary.pid

