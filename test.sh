output_dir=$1
i=0
while [ $i -lt 5 ]
do
	echo $i
	sleep 2
    i=$((i+1))
done
echo "done" > $output_dir/done.txt
