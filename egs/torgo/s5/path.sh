#!/usr/bin/env bash

host=`hostname -f`

export KALDI_ROOT=`pwd`/../../..
if [ ${host#*.} == "windows.dcs.shef.ac.uk" ]; then
    export TORGO_ROOT="$HOME/data/TORGO_original/"
    export REC_ROOT="."
fi

export PATH=$PWD/utils/:$KALDI_ROOT/src/bin:$KALDI_ROOT/tools/openfst/bin:$KALDI_ROOT/src/fstbin/:$KALDI_ROOT/src/gmmbin/:$KALDI_ROOT/src/featbin/:$KALDI_ROOT/src/lm/:$KALDI_ROOT/src/sgmmbin/:$KALDI_ROOT/src/sgmm2bin/:$KALDI_ROOT/src/fgmmbin/:$KALDI_ROOT/src/latbin/:$KALDI_ROOT/src/nnetbin:$KALDI_ROOT/src/nnet2bin:$KALDI_ROOT/src/online2bin/:$KALDI_ROOT/src/ivectorbin/:$KALDI_ROOT/src/lmbin/:$PWD:$PATH:$KALDI_ROOT/tools/sph2pipe_v2.5
export LC_ALL=C
