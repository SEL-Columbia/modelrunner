#!/bin/bash

input_dir=$1
output_dir=$2

echo "reading input from $input_dir"
source activate sequencer
# Get source dir and run py script from there
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
python $DIR/mvmax_sequencer.py -i $input_dir -o $output_dir
