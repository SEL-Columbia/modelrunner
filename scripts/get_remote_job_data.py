#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import re
import requests
import os
import json


def key_val(s):
    try:
        key, val = s.split(':')
        return key, val
    except:
        raise argparse.ArgumentTypeError("Key Vals must be key:val")


def retrieve_job_file(job_dict, job_file, job_data_dir, timeout=0.1):
    """
    given the job dict, determine how to retrieve its log
    and try to fetch and store in job_data_dir
    """
    on_prim = job_dict.get('on_primary', False)
    prefix = 'primary' if on_prim else 'worker'
    top_url = job_dict[prefix + '_url']
    data_dir = job_dict[prefix + '_data_dir']
    uuid = job_dict['uuid']
    file_url = '{}/{}/{}/{}'.format(top_url, data_dir, uuid, job_file)

    local_file = os.path.join(job_data_dir, uuid, job_file)
    response = requests.get(file_url, stream=True, timeout=timeout)
    if not response.ok:
        raise requests.HTTPError(
            "{} had error code {}".format(file_url, response.status_code))

    if not os.path.exists(os.path.dirname(local_file)):
        os.makedirs(os.path.dirname(local_file))

    with open(local_file, 'w') as local_file_stream:
        for block in response.iter_content(1024):
            local_file_stream.write(block)


def filter_by_key_val_regex(job_dict, key_val_tuples):
    result = True
    for key, val in key_val_tuples:
        result = (
            bool(re.match(val.encode('string-escape'), job_dict[key])) and
            result)

    return result


parser = argparse.ArgumentParser(
            description="Get job info from modelrunner instance api")
parser.add_argument("--url",
                    default="http://modelrunner.io",
                    help="full url of modelrunner instance")
parser.add_argument("--key_val_matches",  type=key_val, nargs='*',
                    help="if specified, these regex filters determine which "
                         "jobs to retrieve files for")

# Only relevant for job file retrieval
parser.add_argument("--timeout",
                    default=0.1,
                    help="timeout in seconds of each file request")
parser.add_argument("--job_data_dir",
                    default="job_data",
                    help="directory to store job files")
parser.add_argument("--file_names",
                    nargs='+',
                    help="files from job to retrieve")

args = parser.parse_args()

headers = {'Accept': 'application/json'}
url = re.sub(r'/$', '', args.url) + '/jobs'

response = requests.get(url, headers=headers)
jobs = response.json()['data']

# apply filter
if args.key_val_matches:
    def kv_filter(job_dict):
        return filter_by_key_val_regex(job_dict, args.key_val_matches)

    jobs = filter(kv_filter, jobs)

jobs.sort(key=lambda job: job['created'], reverse=True)

# check if we have files to retrieve
if args.file_names:
    for i in range(0, len(jobs)):
        for f in args.file_names:
            try:
                retrieve_job_file(jobs[i], f, args.job_data_dir, args.timeout)
            except Exception as e:
                print(e)
                print("Failed to retrieve {} for job {}", (f, jobs[i]['uuid']))
            else:
                print("Success retrieving {} for job {}", (f, jobs[i]['uuid']))

else:
    # just print out jobs
    print(json.dumps(jobs, sort_keys=True, indent=4, separators=(',', ': ')))
