#!/bin/bash

source $HOME/.bash_profile

# clear out environment
rm -rf $HOME/miniconda/envs/modelrunner

conda config --set always_yes yes --set changeps1 no
conda create -n modelrunner python=3

cd modelrunner
source activate modelrunner
python setup.py install 
# redis and redis-py are not part of setup install
conda install redis redis-py
