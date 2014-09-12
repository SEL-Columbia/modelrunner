#!/bin/bash

input_dir=$1
output_dir=$2

echo "reading input from $input_dir"
cd models/Sequencer
source activate sequencer
python mvmax_sequencer.py -i $input_dir -o $output_dir
