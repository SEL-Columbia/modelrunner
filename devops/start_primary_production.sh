#!/bin/bash

# start all processes in support of primary server in background
# assumes model_runner conda environment has been activated
redis-server > redis.log 2>&1 & echo $! > redis.pid 
python job_server.py --port=8080 > job_server.log 2>&1 & echo $! > job_server.pid
python job_primary.py > job_primary.log 2>&1 & echo $! > job_primary.pid
# TODO:  Make sure nginx is running
