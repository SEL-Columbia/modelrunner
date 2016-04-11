#!/bin/bash

# start all processes in support of primary server in background
# assumes modelrunner conda environment has been activated
redis-server > redis.log 2>&1 & echo $! > redis.pid 
job_server.py --port=8080 > job_server.log 2>&1 & echo $! > job_server.pid
python -m SimpleHTTPServer 8000 > primary_static_server.log 2>&1 & echo $! > primary_static_server.pid
job_primary.py > job_primary.log 2>&1 & echo $! > job_primary.pid
