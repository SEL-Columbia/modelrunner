#!/bin/bash

# clear out environment
rm -rf $HOME/miniconda/envs/modelrunner

conda config --set always_yes yes --set changeps1 no
conda create -n modelrunner --file modelrunner/requirements.txt

