cd modelrunner
export PATH="$HOME/miniconda/bin:$PATH"
source activate modelrunner
./scripts/start_primary.sh
./scripts/start_worker.sh
