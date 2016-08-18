#!/bin/bash

if [ -e redis.pid ]
then
    kill -s TERM `cat redis.pid`
    rm redis.pid
fi
