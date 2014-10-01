#!/bin/bash

# full test, meant to be run from parent dir as in "$ ./testing/test_full.sh"
# fail on any command failure
set -e

# kick off a job
echo "create new job"
curl -s -F "job_name=test_`date +%Y-%m-%d_%H:%M:%S`" -F "model=test" -F "zip_file=@testing/input.zip" http://localhost:8080/jobs > response
cat response
cat response |  python -c 'import sys, json; print json.load(sys.stdin)["message"]' | grep OK
job_id=`cat response |  python -c 'import sys, json; print json.load(sys.stdin)["id"]'`
echo "job id $job_id created"

# wait 12 seconds and test if it's complete
sleep 12
echo "checking job id $job_id status"
curl -s http://localhost:8080/jobs/$job_id > response
cat response
cat response |  python -c 'import sys, json; print json.load(sys.stdin)["status"]' | grep COMPLETE
echo "job id $job_id completed OK"

# kick off another job to be killed
echo "create job to be killed"
curl -s -F "job_name=test_kill_`date +%Y-%m-%d_%H:%M:%S`" -F "model=test" -F "zip_file=@testing/input.zip" http://localhost:8080/jobs > response
cat response |  python -c 'import sys, json; print json.load(sys.stdin)["message"]' | grep OK
job_id=`cat response |  python -c 'import sys, json; print json.load(sys.stdin)["id"]'`
echo "job id $job_id created"

# wait until status is RUNNING before kill
# unset fail on error
set +e
status=""
MAX_TRIES=20
tries=0
echo "waiting for job $job_id to run"
while [ "$status" != "RUNNING" -a $tries -lt $MAX_TRIES ]
do
  sleep 1
  curl -s http://localhost:8080/jobs/$job_id > response
  status=`cat response |  python -c 'import sys, json; print json.load(sys.stdin)["status"]'`
  let tries++
done
if [ $tries -ge $MAX_TRIES ]
then
  echo "job $job_id stuck in $status state.  Expected it to go to RUNNING"
  exit 1
fi
echo "job $job_id is running"

# test the kill
echo "attempt to kill job $job_id"
curl -s http://localhost:8080/jobs/$job_id/kill > response
cat response |  python -c 'import sys, json; print json.load(sys.stdin)["message"]' | grep OK
echo "kill job $job_id sent"
# ensure that eventually the status of the killed job goes to "FAILED"
tries=0
echo "waiting for job $job_id to be killed"
while [ "$status" != "FAILED" -a $tries -lt $MAX_TRIES ]
do
  sleep 1
  curl -s http://localhost:8080/jobs/$job_id > response
  status=`cat response |  python -c 'import sys, json; print json.load(sys.stdin)["status"]'`
  let tries++
done
if [ $tries -ge $MAX_TRIES ]
then
  echo "job $job_id stuck in $status state.  Expected it to go to FAILED"
  exit 1
fi
echo "job $job_id successfully killed"
echo "SUCCESS"
