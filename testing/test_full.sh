#!/bin/bash

# full test, meant to be run from parent dir as in "$ ./testing/test_full.sh localhost"

# fail on any command failure
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

# kick off a job
echo "creating new job"
job_id=$(mr_create_job test_full_`date +%Y-%m-%d_%H:%M:%S` "test" "@testing/input.zip")

# wait 12 seconds and test if it's complete
echo "checking that job $job_id completes"
mr_wait_for_status $job_id "COMPLETE" 12

# kick off another job to be killed
echo "creating job to be killed"
job_kill_id=$(mr_create_job test_full_kill_`date +%Y-%m-%d_%H:%M:%S` "test" "@testing/input.zip")

echo "waiting for job $job_kill_id to go RUNNING"
mr_wait_for_status $job_kill_id "RUNNING" 2 

# test the kill
echo "attempting to kill job $job_kill_id"
mr_kill_job $job_kill_id

# ensure that eventually the status of the killed job goes to "FAILED"
echo "waiting for job $job_kill_id to go FAILED"
mr_wait_for_status $job_kill_id "FAILED" 2

# disable the trap now
trap - EXIT
mr_cleanup
echo "SUCCESS"
