#!/bin/bash

input_dir=$1
output_dir=$2

echo "reading input from $input_dir"
source activate sequencer
python mvmax_sequencer.py -i $input_dir -o $output_dir
