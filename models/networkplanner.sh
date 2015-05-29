#!/bin/bash
# Run networkplanner via networker given input, output and config

input_dir=$1
output_dir=$2

echo "Running networkplanner"
echo "reading input from $input_dir"
source activate networker
run_networkplanner.py config.json -w $input_dir -o $output_dir
