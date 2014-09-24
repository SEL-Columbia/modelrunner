#!/bin/bash

input_dir=$1
output_dir=$2

# count SECONDS seconds and write ouput
export COUNT_SECONDS=8

ls $input_dir

i=0
while (( i < COUNT_SECONDS ))
do
    echo $i
	sleep 1
    let i++
done
echo "output" > $output_dir/output.txt
