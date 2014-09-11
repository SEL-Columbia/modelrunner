input_dir=$1
output_dir=$2

ls $input_dir
i=0
while [ $i -lt 10 ]
do
	echo $i
	sleep 2
    i=$((i+1))
done
echo "done" > $output_dir/done.txt
