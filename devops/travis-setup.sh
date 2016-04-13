git clone https://github.com/SEL-Columbia/modelrunner
wget https://repo.continuum.io/miniconda/Miniconda-latest-Linux-x86_64.sh -O miniconda.sh
bash miniconda.sh -b -p $HOME/miniconda
hash -r
conda config --set always_yes yes --set changeps1 no
conda update -q conda
conda info -a
conda create -n modelrunner python=2.7
conda install --yes -c https://conda.anaconda.org/sel -n modelrunner modelrunner
