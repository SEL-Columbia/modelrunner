#!/bin/bash
#
# "Test" model script for modelrunner
# Takes its time to write output to a text file
#
# Demonstrates the general structure of a model script to be used with
# modelrunner.  
# Args:
#   input_dir:  directory where model should get input data 
#   output_dir:  directory to put output files
#
# modelrunner takes care of unzipping input and zipping output prior
# to invoking these scripts
 
input_dir=$1
output_dir=$2

# get count of times to sleep
count_sleeps=$( cat $input_dir/sleep_count )

ls $input_dir

i=0
while [ $i -lt $count_sleeps ]
do
    echo $i
    sleep 1
    let i++
done
echo "output" > $output_dir/output.txt
