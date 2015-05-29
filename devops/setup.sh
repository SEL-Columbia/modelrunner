#!/bin/bash

if ! conda &> /dev/null
then
    mkdir -p build; cd build
    echo "Download and install miniconda for python 2.7"
    if [[ ! -e Miniconda-latest-Linux-x86_64.sh ]]
    then
        curl -s -o Miniconda-latest-Linux-x86_64.sh https://repo.continuum.io/miniconda/Miniconda-latest-Linux-x86_64.sh
        chmod 755 Miniconda-latest-Linux-x86_64.sh
    fi
    ./Miniconda-latest-Linux-x86_64.sh -b -p $HOME/miniconda
    cd
    grep "$HOME/miniconda/bin:" .bashrc || echo "export PATH=\"$HOME/miniconda/bin:$PATH\"" >> .bashrc
fi

# bashrc may not have been sourced if run from remote
export PATH="$HOME/miniconda/bin:$PATH"

conda config --set always_yes yes --set changeps1 no
conda update -q conda

# need conda build
conda install conda-build
