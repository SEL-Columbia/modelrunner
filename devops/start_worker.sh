#!/bin/bash

# start all processes in support of worker server in background
# assumes model_runner conda environment has been activated
nohup python -m SimpleHTTPServer 8888 > worker_static_server.log 2>&1 & echo $! > worker_static_server.pid
nohup python job_worker.py --model=test --data_dir=worker_data --worker_is_primary=False > job_worker.log 2>&1 & echo $! > job_worker.pid
