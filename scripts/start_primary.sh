#!/bin/bash

# start all processes in support of primary server in background
# assumes modelrunner conda environment has been activated
# and that redis-server has been started
job_server.py --port=8080 > job_server.log 2>&1 & echo $! > job_server.pid
if python -c 'import http.server' > /dev/null 2>&1
then
    python -m http.server 8000 > primary_static_server.log 2>&1 & echo $! > primary_static_server.pid
else
    python -m SimpleHTTPServer 8000 > primary_static_server.log 2>&1 & echo $! > primary_static_server.pid
fi

job_primary.py > job_primary.log 2>&1 & echo $! > job_primary.pid
