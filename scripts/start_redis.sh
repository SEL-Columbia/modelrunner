#!/bin/bash

# start redis server process
# assumes modelrunner conda environment has been activated
if [ -e redis.conf ]
then
    redis-server redis.conf > redis.log 2>&1 &
else
    redis-server > redis.log 2>&1 &
fi
