#!/bin/bash

# start all processes in support of primary server in background
# assumes modelrunner conda environment has been activated
job_server.py --port=8080 > job_server.log 2>&1 & echo $! > job_server.pid
job_primary.py > job_primary.log 2>&1 & echo $! > job_primary.pid

# restart nginx for production static server
# assumes we're in modelrunner dir
sudo rm -f /etc/nginx/sites-enabled/*
sudo cp devops/primary.nginx /etc/nginx/sites-available/primary
sudo ln -s /etc/nginx/sites-available/primary /etc/nginx/sites-enabled/
sudo service nginx restart 
