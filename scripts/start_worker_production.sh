#!/bin/bash

# start all processes in support of worker server in background
# assumes modelrunner conda environment has been activated
job_worker.py --model=sequencer --data_dir=worker_data > job_worker_sequencer.log 2>&1 & echo $! > job_worker_sequencer.pid
job_worker.py --model=networker --data_dir=worker_data > job_worker_networker.log 2>&1 & echo $! > job_worker_networker.pid
job_worker.py --model=networkplanner --data_dir=worker_data > job_worker_networkplanner.log 2>&1 & echo $! > job_worker_networkplanner.pid
job_worker.py --model=test --data_dir=worker_data > job_worker_test.log 2>&1 & echo $! > job_worker_test.pid

# restart nginx for production static server
# assumes we're in modelrunner dir
sudo rm -f /etc/nginx/sites-enabled/*
sudo cp devops/worker.nginx /etc/nginx/sites-available/worker
sudo ln -s /etc/nginx/sites-available/worker /etc/nginx/sites-enabled/
sudo service nginx restart 
