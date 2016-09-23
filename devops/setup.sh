#!/bin/bash

# curl for getting conda, nginx for static server (production only)
# gcc and python-dev for psutil
sudo apt-get install -y curl nginx gcc python-dev

if ! conda &> /dev/null
then
    mkdir -p build; cd build
    echo "Download and install miniconda for python"
    if [[ ! -e Miniconda-latest-Linux-x86_64.sh ]]
    then
        curl -s -o Miniconda-latest-Linux-x86_64.sh https://repo.continuum.io/miniconda/Miniconda-latest-Linux-x86_64.sh
        chmod 755 Miniconda-latest-Linux-x86_64.sh
    fi
    ./Miniconda-latest-Linux-x86_64.sh -b -p $HOME/miniconda
    cd
    grep "$HOME/miniconda/bin:" .bashrc || echo "export PATH=\"$HOME/miniconda/bin:$PATH\"" >> .bashrc
    grep "$HOME/miniconda/bin:" .bash_profile || echo "export PATH=\"$HOME/miniconda/bin:$PATH\"" >> .bash_profile
fi

# bashrc may not have been sourced if run from remote
export PATH="$HOME/miniconda/bin:$PATH"

conda config --set always_yes yes
conda update -q conda
