cd modelrunner
export PATH="$HOME/miniconda/bin:$PATH"
echo "in script"
sleep 1
for pid_file in *.pid; do p=`cat $pid_file`; echo "$pid_file $p"; done
./testing/test_full.sh localhost:8080
./testing/test_queueing.sh localhost:8080
