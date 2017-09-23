#!/bin/bash

source $HOME/.bash_profile
# so that conda doesn't exit after running
conda config --set always_yes yes

# NOTE:  the repo is named infrastructure-planning, but model is
# referred to as electrificationplanner in modelrunner
echo "Setup electrificationplanner env"
# electrificationplanner requires full source to run
rm -rf $HOME/infrastructure-planning
git clone https://github.com/SEL-Columbia/infrastructure-planning

# install dependencies
rm -rf $HOME/miniconda/envs/electrificationplanner
conda create -n electrificationplanner python=2.7
conda install -n electrificationplanner --override-channels -c conda-forge -c sel gdal infrastructure-planning
