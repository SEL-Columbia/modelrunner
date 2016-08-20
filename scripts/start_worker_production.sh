#!/bin/bash
# Start worker for model

if [ "$#" -ne 1 ]
then
    echo "Usage: start_worker_production.sh model"
    exit 1
fi

model=$1

# start process in support of worker server in background
# assumes modelrunner conda environment has been activated
if [ -f job_worker_$model.pid ]
then
    echo "worker for model $model already started, skipping..."
else
    job_worker.py --model=$model --data_dir=worker_data > job_worker_$model.log 2>&1 & echo $! > job_worker_$model.pid
fi

# restart nginx for production static server
# assumes we're in modelrunner dir
sudo rm -f /etc/nginx/sites-enabled/*
sudo cp devops/worker.nginx /etc/nginx/sites-available/worker
sudo ln -s /etc/nginx/sites-available/worker /etc/nginx/sites-enabled/
sudo service nginx restart 
