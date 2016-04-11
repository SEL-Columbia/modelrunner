#!/bin/bash
# Run networker with given input, output and config

input_dir=$1
output_dir=$2

echo "Running networker"
echo "reading input from $input_dir"
source activate networker
run_networker.py config.json -w $input_dir -o $output_dir
