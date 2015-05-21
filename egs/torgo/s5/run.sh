#!/usr/bin/env bash
#
# TORGO Database of Dysarthric Articulation
# https://catalog.ldc.upenn.edu/LDC2012S02
#
# Recipe based on the TEDLium recipe in $KALDI_ROOT/egs/tedlium
#
# Copyright  2015 University of Sheffield (Author: Ricard Marxer)
#
# Apache 2.0
#

. cmd.sh
. path.sh

nj=40
decode_nj=8

stage=0
overwrite=false

. utils/parse_options.sh # accept options

overwrite_flag=""
if [ "$overwrite" = true ]; then
    overwrite_flag="--overwrite"
fi

# Data preparation
if [ $stage -le 0 ]; then
  local/parse_torgo.py $overwrite_flag $TORGO_ROOT $REC_ROOT/tmp/torgo.json || exit 1

  local/prepare_data.py $REC_ROOT/tmp/torgo.json $REC_ROOT  || exit 1

  #local/prepare_dict.sh || exit 1

  #utils/prepare_lang.sh data/local/dict_nosp \
  #  "<UNK>" data/local/lang_nosp data/lang_nosp || exit 1

  #local/prepare_lm.sh || exit 1

fi
