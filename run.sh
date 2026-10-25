#!/bin/bash
#PBS -N pab
#PBS -m abe
#PBS -q testes
#PBS -M j215217@dac.unicamp.br

cd "$PBS_O_WORKDIR"

source "$WORKDIR/spack/share/spack/setup-env.sh"
spack env activate pab
source .venv/bin/activate
python run.py database.db benchmark.yaml
