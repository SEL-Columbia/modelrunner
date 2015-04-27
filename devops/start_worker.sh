#!/bin/bash

# start all processes in support of worker server in background
# assumes model_runner conda environment has been activated
python -m SimpleHTTPServer 8888 > worker_static_server.log 2>&1 & echo $! > worker_static_server.pid
python job_worker.py --model=sequencer --data_dir=worker_data > job_worker_sequencer.log 2>&1 & echo $! > job_worker_sequencer.pid
python job_worker.py --model=networker --data_dir=worker_data > job_worker_networker.log 2>&1 & echo $! > job_worker_networker.pid
python job_worker.py --model=networkplanner --data_dir=worker_data > job_worker_networkplanner.log 2>&1 & echo $! > job_worker_networkplanner.pid
python job_worker.py --model=test --data_dir=worker_data > job_worker_test.log 2>&1 & echo $! > job_worker_test.pid
