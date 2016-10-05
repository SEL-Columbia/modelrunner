#!/bin/bash
#
# Run the sequencer model

input_dir=$1
output_dir=$2

echo "Running sequencer"
echo "reading input from $input_dir"
source activate sequencer

# if we have a config file, use that
# otherwise, use explicitly named input files (legacy usage)
if [[ -f config.json ]]
then
    run_sequencer.py -c config.json -w $input_dir -o $output_dir
else
    run_sequencer.py -w $input_dir -m metrics-local.csv -n networks-proposed.shp -d "Demand...Projected.nodal.demand.per.year" -p "Population" -o output
fi
