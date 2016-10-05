#!/bin/bash

source $HOME/.bash_profile

# so that conda doesn't exit after running
conda config --set always_yes yes

# I believe this is needed if we re-upload sequencer and
# don't change the version in the meta.yaml
rm -rf $HOME/miniconda/pkgs/sequencer*

echo "Setup Sequencer env"
rm -rf $HOME/miniconda/envs/sequencer
conda create -n sequencer python=2.7
conda install -n sequencer -c sel sequencer
