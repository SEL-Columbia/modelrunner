#!/bin/bash

source $HOME/.bash_profile

# clear out environment
rm -rf $HOME/miniconda/envs/modelrunner

conda config --set always_yes yes --set changeps1 no
conda create -n modelrunner python=2.7

cd modelrunner
source activate modelrunner
python setup.py develop
# redis and redis-py are not part in setup install
# so add them here
conda install redis redis-py
