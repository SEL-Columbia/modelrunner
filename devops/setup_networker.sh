#!/bin/bash

source $HOME/.bash_profile
# so that conda doesn't exit after running
conda config --set always_yes yes

echo "Setup Networker env"
rm -rf $HOME/miniconda/envs/networker
conda create -n networker python=2.7
conda install -n networker -c conda-forge -c sel networker
