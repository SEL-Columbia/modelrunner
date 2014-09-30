#!/bin/bash

# expand unexpanded globs into a null list
shopt -s nullglob
# Stop all processes
for pid_file in *.pid
do
    pid=`cat $pid_file`
    echo "kill $pid from $pid_file"
    kill -s TERM $pid
    rm $pid_file
done
