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

. utils/parse_options.sh # accept options

mkdir -p ${REC_ROOT}

overwrite_flag=""
if [ "$overwrite" = true ]; then
    overwrite_flag="--overwrite"
fi

# Data preparation
if [ ${stage} -le 0 ]; then
  local/parse_uaspeech.py ${overwrite_flag} ${UASPEECH_ROOT} ${REC_ROOT}/tmp/uaspeech.json || exit 1

  local/prepare_data.py ${REC_ROOT}/tmp/uaspeech.json ${REC_ROOT}  || exit 1

  local/prepare_dict_cmudict.py ${REC_ROOT}/tmp/dict || exit 1

  utils/prepare_lang.sh ${REC_ROOT}/tmp/dict "<UNK>" ${REC_ROOT}/tmp/lang ${REC_ROOT}/data/lang || exit 1

  local/prepare_lm_anyword.py ${REC_ROOT}/data/lang ${REC_ROOT}/data/lang/words.txt ${REC_ROOT}/data/lang_largevocab_test || exit 1

fi


# Feature extraction
feat_dir=${REC_ROOT}/data/mfcc_features
if [ ${stage} -le 1 ]; then
  for set in train test; do
    dir=${REC_ROOT}/data/$set
    steps/make_mfcc.sh --nj $nj --cmd "$train_cmd" $dir $dir/log $dir/data || exit 1
    steps/compute_cmvn_stats.sh $dir $dir/log $dir/data || exit 1
  done
fi


# Train monophone model
if [ ${stage} -le 2 ]; then
  steps/train_mono.sh --nj $nj --cmd "$train_cmd" \
    ${REC_ROOT}/data/train ${REC_ROOT}/data/lang ${REC_ROOT}/exp/mono0a || exit 1

  steps/align_si.sh --nj $nj --cmd "$train_cmd" \
    ${REC_ROOT}/data/train ${REC_ROOT}/data/lang ${REC_ROOT}/exp/mono0a ${REC_ROOT}/exp/mono0a_ali || exit 1

  steps/train_deltas.sh --cmd "$train_cmd" \
    2500 30000 ${REC_ROOT}/data/train ${REC_ROOT}/data/lang ${REC_ROOT}/exp/mono0a_ali ${REC_ROOT}/exp/tri1 || exit 1
fi


# Decode monophone model
if [ ${stage} -le 3 ]; then
  utils/mkgraph.sh ${REC_ROOT}/data/lang_largevocab_test ${REC_ROOT}/exp/tri1 ${REC_ROOT}/exp/tri1/graph_largevocab || exit 1

  steps/decode_fmllr.sh --nj ${decode_nj} --cmd "$decode_cmd" \
    --num-threads 4 --parallel-opts "${parallel_opts}" \
    ${REC_ROOT}/exp/tri1/graph_largevocab ${REC_ROOT}/data/test ${REC_ROOT}/exp/tri1/decode_largevocab_test || exit 1
fi


# Train triphone models
if [ ${stage} -le 2 ]; then
  steps/align_si.sh --nj $nj \
    ${REC_ROOT}/data/train ${REC_ROOT}/data/lang ${REC_ROOT}/exp/tri1 ${REC_ROOT}/exp/tri1_ali || exit 1;

  steps/train_lda_mllt.sh \
    --splice-opts "--left-context=3 --right-context=3" \
    2500 15000 ${REC_ROOT}/data/train ${REC_ROOT}/data/lang ${REC_ROOT}/exp/tri1_ali ${REC_ROOT}/exp/tri2b || exit 1;

  steps/align_si.sh  --nj $nj \
    --use-graphs true ${REC_ROOT}/data/train ${REC_ROOT}/data/lang ${REC_ROOT}/exp/tri2b ${REC_ROOT}/exp/tri2b_ali  || exit 1;

  steps/train_sat.sh \
    2500 15000 ${REC_ROOT}/data/train ${REC_ROOT}/data/lang ${REC_ROOT}/exp/tri2b_ali ${REC_ROOT}/exp/tri3b || exit 1;
fi


# Decode triphone models
if [ ${stage} -le 3 ]; then
  utils/mkgraph.sh ${REC_ROOT}/data/lang_largevocab_test ${REC_ROOT}/exp/tri3b ${REC_ROOT}/exp/tri3b/graph_largevocab || exit 1;

  steps/decode_fmllr.sh --nj ${decode_nj} --cmd "$decode_cmd" \
    --num-threads 4 --parallel-opts "${parallel_opts}" \
    ${REC_ROOT}/exp/tri3b/graph_largevocab ${REC_ROOT}/data/test ${REC_ROOT}/exp/tri3b/decode_largevocab_test || exit 1

  utils/mkgraph.sh ${REC_ROOT}/data/lang_largevocab_test ${REC_ROOT}/exp/tri3b ${REC_ROOT}/exp/tri3b/graph_largevocab || exit 1;

  steps/decode_fmllr.sh --nj ${decode_nj} --cmd "$decode_cmd" \
    --num-threads 4 --parallel-opts "${parallel_opts}" \
    ${REC_ROOT}/exp/tri3b/graph_largevocab ${REC_ROOT}/data/test ${REC_ROOT}/exp/tri3b/decode_largevocab_test || exit 1
fi
