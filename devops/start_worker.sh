#!/bin/bash

# start all processes in support of worker server in background
# assumes model_runner conda environment has been activated
python -m SimpleHTTPServer 8888 > worker_static_server.log 2>&1 & echo $! > worker_static_server.pid
python job_worker.py --model=sequence --data_dir=worker_data > job_worker_sequence.log 2>&1 & echo $! > job_worker_sequence.pid
python job_worker.py --model=test --data_dir=worker_data > job_worker_test.log 2>&1 & echo $! > job_worker_test.pid
