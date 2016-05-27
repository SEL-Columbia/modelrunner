#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import re
import requests
import os

parser = argparse.ArgumentParser(description="Get jobs as list from modelrunner instance api")
parser.add_argument("--url", 
                    default="http://modelrunner.io",
                    help="full url of modelrunner instance")
parser.add_argument("--job_log_dir", 
                    default="job_logs",
                    help="directory to store job logs")
parser.add_argument("--key_val_matches", 
                    nargs='*',
                    help="if specified, these regex filters determine which jobs to retrieve logs for")

def retrieve_job_log(job_dict, job_log_dir):
    """
    given the job dict, determine how to retrieve its log
    and try to fetch store in job_log_dir
    """
    on_prim = job_dict.get('on_primary', False)
    prefix = 'primary' if on_prim else 'worker'
    top_url = job_dict[prefix + '_url']
    data_dir = job_dict[prefix + '_data_dir']
    uuid = job_dict['uuid']
    log_url = '{}/{}/{}/job_log.txt'.format(top_url, data_dir, uuid)

    local_log_file = os.path.join(job_log_dir, uuid, 'job_log.txt')
    try:
        response = requests.get(log_url, stream=True)
        if not response.ok:
            raise requests.HTTPError("{} had error code {}".format(log_url, response.status_code))

        if not os.path.exists(os.path.dirname(local_log_file)):
            os.makedirs(os.path.dirname(local_log_file))

        with open(local_log_file, 'w') as local_log:
            for block in response.iter_content(1024):
                local_log.write(block)

    except Exception as e:
        print(e)
        print("Failed to retrieve job_log for job {}", uuid)
    
args = parser.parse_args()

headers = {'Accept': 'application/json'}
url = re.sub(r'/$', '', args.url) + '/jobs'

response = requests.get(url, headers=headers)
jobs = response.json()['data']

jobs.sort(key=lambda job: job['created'], reverse=True)

for i in range(0, min(5, len(jobs))):
    retrieve_job_log(jobs[i], args.job_log_dir)
