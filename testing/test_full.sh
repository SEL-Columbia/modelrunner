#!/bin/bash

# full test, meant to be run from parent dir as in "$ ./testing/test_full.sh localhost"

# fail on any command failure
set -e

# get test server as param
if [ $# -lt 1 ]
then
  echo "Usage: ${0##*/} test_server_url"
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

# ensure that job list is empty to start
echo "checking that there are no jobs yet"
num_jobs=$(mr_get_jobs | python -c "import sys, json; print(len(json.load(sys.stdin)[\"data\"]))")
if [ $num_jobs -ne 0 ]
then
    exit 1
fi

# kick off a job
echo "creating new job"
job_id=$(mr_create_job test_full_`date +%Y-%m-%d_%H:%M:%S` "test" "@testing/sleep_count_8.zip")

# wait 12 seconds and test if it's complete
echo "checking that job $job_id completes"
mr_wait_for_status $job_id "COMPLETE" 12

# kick off another job to be killed
echo "creating job to be killed"
job_kill_id=$(mr_create_job test_full_kill_`date +%Y-%m-%d_%H:%M:%S` "test" "@testing/sleep_count_30.zip")

echo "waiting for job $job_kill_id to go RUNNING"
mr_wait_for_status $job_kill_id "RUNNING" 2 

# test the kill
echo "attempting to kill job $job_kill_id"
mr_kill_job $job_kill_id

# ensure that eventually the status of the killed job goes to "KILLED"
echo "waiting for job $job_kill_id to go KILLED"
mr_wait_for_status $job_kill_id "KILLED" 2

# ensure that we can kill 2nd job while 1st job is running
echo "creating long running job"
job_long_id=$(mr_create_job test_long_`date +%Y-%m-%d_%H:%M:%S` "test" "@testing/sleep_count_30.zip")

echo "creating 2nd job for separate model to be killed"
job_2_id=$(mr_create_job test_2_`date +%Y-%m-%d_%H:%M:%S` "test_2" "@testing/sleep_count_8.zip")

echo "waiting for job $job_2_id to go RUNNING"
mr_wait_for_status $job_2_id "RUNNING" 2 

# test the kill
echo "attempting to kill job $job_2_id"
mr_kill_job $job_2_id

echo "waiting for job $job_2_id to go KILLED"
mr_wait_for_status $job_2_id "KILLED" 2

# test killing long running job
echo "attempting to kill job $job_long_id"
mr_kill_job $job_long_id

echo "waiting for job $job_long_id to go KILLED"
mr_wait_for_status $job_long_id "KILLED" 2

# we should have 4 jobs now
echo "checking that there are 4 jobs"
num_jobs=$(mr_get_jobs | python -c "import sys, json; print(len(json.load(sys.stdin)[\"data\"]))")
if [ $num_jobs -ne 4 ]
then
    exit 1
fi

# disable the trap now
trap - EXIT
mr_cleanup
echo "SUCCESS"
