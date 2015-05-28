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

nj=6
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

  local/prepare_dict.py $REC_ROOT/tmp/dict || exit 1

  utils/prepare_lang.sh $REC_ROOT/tmp/dict "<UNK>" $REC_ROOT/tmp/lang $REC_ROOT/data/lang || exit 1

  #local/prepare_lm.sh || exit 1

fi


# Feature extraction
feat_dir=$REC_ROOT/data/mfcc_features
if [ $stage -le 1 ]; then
  for set in test dev train; do
    dir=$REC_ROOT/data/$set
    steps/make_mfcc.sh --nj $nj --cmd "$train_cmd" $dir $dir/log $dir/data || exit 1
    steps/compute_cmvn_stats.sh $dir $dir/log $dir/data || exit 1
  done
fi
