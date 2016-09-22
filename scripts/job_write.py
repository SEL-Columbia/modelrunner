#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script to write job data as csv to Redis DB
"""

import csv
import argparse
import modelrunner
import modelrunner.settings
from modelrunner import Job

parser = argparse.ArgumentParser(description="Write CSV of job data to Redis")
parser.add_argument("--redis_url",
                    default="redis://@localhost:6379",
                    help="URL to connect to Redis")
parser.add_argument("csv_file",
                    help="csv of jobs with header corresponding to Job fields")
args = parser.parse_args()

# initialize the global application settings
modelrunner.settings.initialize(args.redis_url)

with open(args.csv_file) as csvfile:
    reader = csv.DictReader(csvfile)
    for job_dict in reader:
        job = Job(**job_dict)
        Job[job_dict['uuid']] = job

