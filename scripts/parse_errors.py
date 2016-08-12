#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import sys
import itertools
import argparse

description = """
              Parse and aggregate errors from python model logs
              (passed to stdin line by line)

              Outputs a csv of error records if no --aggregate_fields

              Otherwise, outputs aggregate errors/counts
              """


def format_csv_cell(cell_string):
    new_cell = '"%s"' % (re.sub(r'"', '\\"', cell_string))
    return new_cell


parser = argparse.ArgumentParser(description=description)
parser.add_argument("--aggregate_fields",
                    nargs='+',
                    help="aggregate records by fields")
args = parser.parse_args()

# load up error records
records = []
for log_file in sys.stdin:
    record = dict()
    with open(log_file.strip(), 'r') as log_stream:
        for line in log_stream:
            line = line.strip('\n')
            # Keep last python error file ref before error
            if re.search(r'^  File', line):
                model_dict = dict()
                m = re.search(r'envs/(?P<model>[^/]*)', line)
                if m:
                    model_dict.update(m.groupdict())
                else:
                    model_dict['model'] = 'modelrunner'

                m = re.search(
                        r'/(?P<py_file>[^"]*)", line (?P<py_line>\d*)',
                        line)

                model_dict.update(m.groupdict())
                record.update(model_dict)

            last_line = line

        if re.search(r'Error', last_line):
            m = re.search(
                    r'(?P<error_code>[^:]*)(: (?P<error_msg>.*))?$',
                    last_line)

            record.update(m.groupdict())
            records.append(record)

# output 'em
if len(records) > 0:
    if args.aggregate_fields:

        def key_fun(rec):
            return " ".join(map(rec.get, args.aggregate_fields))

        records.sort(key=key_fun)
        for key, group in itertools.groupby(records, key_fun):
            print("%s,%s" % (key, len(list(group))))
    else:
        keys = sorted(records[0].keys())
        print(",".join(keys))
        for record in records:
            print(",".join(map(
                            lambda k:
                            format_csv_cell(str(record.get(k, ''))),
                            keys)))
