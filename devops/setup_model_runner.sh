#!/bin/bash

# clear out environment
rm -rf /home/mr/miniconda/envs/model_runner

conda config --set always_yes yes --set changeps1 no
conda create -n model_runner --file model_runner/requirements.txt

