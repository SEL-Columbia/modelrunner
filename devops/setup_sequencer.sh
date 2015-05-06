#!/bin/bash
# so that conda doesn't exit after running
conda config --set always_yes yes --set changeps1 no

# legacy cleanup, shouldn't be needed soon
rm -rf $HOME/miniconda/conda-bld/linux-64/sequencer-*.bz2

# I believe this is needed if we re-upload sequencer and
# don't change the version in the meta.yaml
rm -rf $HOME/miniconda/pkgs/sequencer*

echo "Setup Sequencer env"
rm -rf $HOME/miniconda/envs/sequencer
conda create -n sequencer python=2.7
conda install -n sequencer -c sel sequencer
