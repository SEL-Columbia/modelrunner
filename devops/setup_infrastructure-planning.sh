#!/bin/bash

source $HOME/.bash_profile
# so that conda doesn't exit after running
conda config --set always_yes yes

echo "Setup infrastructure-planning env"
# infrastructure-planning requires full source to run
rm -rf $HOME/infrastructure-planning
git clone https://github.com/SEL-Columbia/infrastructure-planning

# install dependencies
rm -rf $HOME/miniconda/envs/infrastructure-planning
conda create -n infrastructure-planning python=2.7
conda install -n infrastructure-planning -c conda-forge -c sel infrastructure-planning
