#!/bin/bash
# Run electrificationplanner with given input, output and config

input_dir=$1
output_dir=$2

echo "Running electrificationplanner"
echo "Reading input from $input_dir"
pushd $HOME/infrastructure-planning
source activate electrificationplanner
python estimate_electricity_cost_by_technology_from_population.py $input_dir/config.json -w $input_dir -o $output_dir
popd
