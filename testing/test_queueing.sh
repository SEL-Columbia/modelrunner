#!/bin/bash

# Test the following
#
# time  action         job1    | job2
# ----------------------------------------
# t1   queue job1 ->   CREATED | 
#  |   queue job2 ->   RUNNING |CREATED
#  V   kill job1  ->   FAILED  |RUNNING
# t4                   FAILED  |COMPLETE

set -e

# get test server as param
if [ $# -lt 1 ]
then
  echo "Usage: ${0##*/} test_server_name"
  exit 1
fi 

# needs to be set so that api_functions work
MR_SERVER=$1
# temp dir to store all working data
MR_TMP_DIR=$(mktemp -d)
# get the source dir for testing so we can source the api_functions
MR_TEST_SRC_DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
. $MR_TEST_SRC_DIR/api_functions.sh

trap mr_cleanup EXIT

echo "creating 2 jobs"
job_1_id=$(mr_create_job test_kill_`date +%Y-%m-%d_%H:%M:%S` "test" "@testing/input.zip")
job_2_id=$(mr_create_job test_queue_`date +%Y-%m-%d_%H:%M:%S` "test" "@testing/input.zip")
echo "created job $job_1_id and job $job_2_id"

echo "killing job $job_1_id"
# wait for job 1 to start, kill it and wait for it to fail
mr_wait_for_status $job_1_id "RUNNING" 10
mr_kill_job $job_1_id
mr_wait_for_status $job_1_id "FAILED" 7
echo "killed job $job_1_id"

# now wait for job 2 to finish
mr_wait_for_status $job_2_id "COMPLETE" 10
echo "completed job $job_2_id"

# disable the trap now
trap - EXIT
mr_cleanup
echo "SUCCESS"
