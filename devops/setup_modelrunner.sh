#!/bin/bash

source $HOME/.bash_profile

# clear out environment
rm -rf $HOME/miniconda/envs/modelrunner

conda config --set always_yes yes --set changeps1 no
conda create -n modelrunner python=3
conda install --yes -c sel -n modelrunner modelrunner
