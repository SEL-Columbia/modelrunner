#!/bin/bash
#
# Functions serving as modelrunner client api
# 
# Assumes the following variables are set for a client "session"
# MR_TMP_DIR:  directory to maintain all tmp data for this session
# MR_SERVER:  modelrunner test server ip or hostname

function mr_cleanup {
    # cleanup working data
    # meant to be called at end of "session"
    rm -rf $MR_TMP_DIR
}

function mr_get_val_from_json {
    # get the value for the key in the stdin stream 
    key=$1
    python -c "import sys, json; print json.load(sys.stdin)[\"$key\"]"
}

function mr_create_job {
    # returns job id if available in response
    local job_name=$1
    local job_model=$2
    local job_file=$3
    # temp file for response
    local tmpfile=$(mktemp -p $MR_TMP_DIR)
    if [[ $job_file =~ ^http[s]?:// ]]
    then
        curl -s -F "job_name=$job_name" -F "model=$job_model" -F "zip_url=$job_file" $MR_SERVER/jobs > $tmpfile
    else
        curl -s -F "job_name=$job_name" -F "model=$job_model" -F "zip_file=$job_file" $MR_SERVER/jobs > $tmpfile
    fi
    # check if call was OK
    cat $tmpfile | mr_get_val_from_json message | grep OK > /dev/null
    cat $tmpfile | mr_get_val_from_json id
}

function mr_kill_job {
    # kill job and ensure that initial response is OK
    local job_id=$1
    local tmpfile=$(mktemp -p $MR_TMP_DIR)
    curl -s $MR_SERVER/jobs/$job_id/kill > $tmpfile
    cat $tmpfile |  mr_get_val_from_json message | grep OK > /dev/null
}

function mr_job_status {
    # get the job status
    local job_id=$1
    local tmpfile=$(mktemp -p $MR_TMP_DIR)
    curl -s $MR_SERVER/jobs/$job_id > $tmpfile
    cat $tmpfile | mr_get_val_from_json status
}

function mr_get_jobs {
    # get the job status
    local tmpfile=$(mktemp -p $MR_TMP_DIR)
    curl -s -H 'Accept: application/json' $MR_SERVER/jobs
}

function mr_wait_for_status {
    # wait for job to change status
    local job_id=$1
    local new_status=$2
    local max_tries=$3
    local job_status=$(mr_job_status $job_id)
    local tries=0
    while [ "$job_status" != "$new_status" -a $tries -lt $max_tries ]
    do
        sleep 1 # wait a second to test again
        job_status=$(mr_job_status $job_id)
        echo "job $job_id current status $job_status"
        tries=$(($tries + 1)) 
        echo "tries $tries"
    done
    if [ $tries -ge $max_tries ]
    then
        echo "job $job_id stuck in $job_status state.  Expected it to go to $new_status"
        exit 1
    fi
}


