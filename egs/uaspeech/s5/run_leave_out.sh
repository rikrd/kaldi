#!/usr/bin/env bash
#
# UASPEECH Database of Dysarthric Articulation
# http://www.isle.illinois.edu/sst/data/UASpeech/
#
# Recipe based on the TEDLium recipe in $KALDI_ROOT/egs/tedlium
#
# Copyright  2015 University of Sheffield (Author: Ricard Marxer)
#
# Apache 2.0
#

. cmd.sh
. path.sh

nj=12
decode_nj=16
parallel_opts=

stage=0
overwrite=false
feature=mfcc
feature_maker=steps/make_mfcc.sh

. utils/parse_options.sh # accept options

mkdir -p ${REC_ROOT}

local/run_split.sh --feature $feature \
  '.speakers as $speakers | .utterances[] | select($speakers[.speaker].type!="control" and .speaker!="M04") | .utterance_id' \
  '.speakers as $speakers | .utterances[] | select($speakers[.speaker].type!="control" and .speaker=="M04" and .block!="2") | .utterance_id' \
  '.speakers as $speakers | .utterances[] | select($speakers[.speaker].type!="control" and .speaker=="M04" and .block=="2") | .utterance_id' \
   ${REC_ROOT}/leave_one_out_M04
