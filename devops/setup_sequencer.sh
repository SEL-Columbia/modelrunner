#!/bin/bash

echo "Setup recipes to be installed"
rm -rf conda-recipes
git clone https://github.com/SEL-Columbia/conda-recipes

# so that conda doesn't exit after running
conda config --set always_yes yes --set changeps1 no

echo "Building Sequencer"
# run in bg because otherwise it exits this process on completion
cd conda-recipes
conda build Sequencer
cd

echo "Setup Sequencer env"
# delete Sequencer and sequencer conda env
rm -rf Sequencer
rm -rf /home/mr/miniconda/envs/sequencer
git clone https://github.com/SEL-Columbia/Sequencer
cd Sequencer
# run in bg because otherwise it exits this process on completion
conda create -n sequencer --file requirements.txt
cd

echo "Install sequencer"
source activate sequencer
conda install -n sequencer --use-local /home/mr/miniconda/conda-bld/linux-64/sequencer--*.bz2
