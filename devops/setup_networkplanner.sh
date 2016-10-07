#!/bin/bash

source $HOME/.bash_profile
# so that conda doesn't exit after running
conda config --set always_yes yes

echo "Setup networkplanner env"
rm -rf $HOME/miniconda/envs/networkplanner
conda create -n networkplanner python=2.7
conda install -n networkplanner -c conda-forge -c sel networkplanner-metrics
conda install -n networkplanner -c conda-forge -c sel networker
