#!/bin/bash
# Start worker for model

if [ "$#" -ne 1 ]
then
    echo "Usage: start_worker.sh model"
    exit 1
fi

model=$1

# start process in support of worker server in background
# assumes modelrunner conda environment has been activated
if [ -f worker_static_server.pid ]
then
    echo "static server already started, skipping..."
elif python -c 'import http.server' > /dev/null 2>&1
then
    python -m http.server 8888 > worker_static_server.log 2>&1 & echo $! > worker_static_server.pid
else
    python -m SimpleHTTPServer 8888 > worker_static_server.log 2>&1 & echo $! > worker_static_server.pid
fi

if [ -f job_worker_$model.pid ]
then
    echo "worker for model $model already started, skipping..."
else
    job_worker.py --model=$model --data_dir=worker_data > job_worker_$model.log 2>&1 & echo $! > job_worker_$model.pid
fi
