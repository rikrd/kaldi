#!/usr/bin/env bash
#
# UASPEECH Database of Dysarthric Articulation
# http://www.isle.illinois.edu/sst/data/UASpeech/
#
# Train the GMM model (monophone flat start -> delta delta -> LDA_MLLT -> SAT)
#
# Copyright  2015 University of Sheffield (Author: Ricard Marxer)
#
# Apache 2.0
#

script_path=`dirname $0`

. ${script_path}/../cmd.sh
. ${script_path}/../path.sh

nj=12
decode_nj=1
parallel_opts=

stage=0
overwrite=false

. ${script_path}/../utils/parse_options.sh # accept options

if [ $# -ne 1 ]; then
  printf "\nUSAGE: %s <directory>\n\n" `basename $0`
  echo "The argument specifies the input and output directory that "
  echo "should contain 'train' and 'test' data dirs in Kaldi format"
  exit 1;
fi

dir=$1

# Train monophone model
if [ ${stage} -le 2 ]; then
  steps/train_mono.sh --nj $nj --cmd "$train_cmd" \
    ${dir}/train ${REC_ROOT}/data/lang ${dir}/exp/mono0a || exit 1

  steps/align_si.sh --nj $nj --cmd "$train_cmd" \
    ${dir}/train ${REC_ROOT}/data/lang ${dir}/exp/mono0a ${dir}/exp/mono0a_ali || exit 1

  steps/train_deltas.sh --cmd "$train_cmd" \
    2500 30000 ${dir}/train ${REC_ROOT}/data/lang ${dir}/exp/mono0a_ali ${dir}/exp/tri1 || exit 1
fi

# Decode monophone model
if [ ${stage} -le 3 ]; then
  utils/mkgraph.sh ${REC_ROOT}/data/lang_largevocab_test ${dir}/exp/tri1 ${dir}/exp/tri1/graph_largevocab || exit 1

  steps/decode_fmllr.sh --nj ${decode_nj} --cmd "$decode_cmd" \
    --num-threads 4 --parallel-opts "${parallel_opts}" \
    --scoring-opts "--min-lmwt 0 --max-lmwt 0" \
    ${dir}/exp/tri1/graph_largevocab ${dir}/test ${dir}/exp/tri1/decode_largevocab_test || exit 1
fi

# Train triphone models
if [ ${stage} -le 2 ]; then
  steps/align_si.sh --nj $nj \
    ${dir}/train ${REC_ROOT}/data/lang ${dir}/exp/tri1 ${dir}/exp/tri1_ali || exit 1;

  steps/train_lda_mllt.sh \
    --splice-opts "--left-context=3 --right-context=3" \
    2500 15000 ${dir}/train ${REC_ROOT}/data/lang ${dir}/exp/tri1_ali ${dir}/exp/tri2b || exit 1;

  steps/align_si.sh  --nj $nj \
    --use-graphs true ${dir}/train ${REC_ROOT}/data/lang ${dir}/exp/tri2b ${dir}/exp/tri2b_ali  || exit 1;

  steps/train_sat.sh \
    2500 15000 ${dir}/train ${REC_ROOT}/data/lang ${dir}/exp/tri2b_ali ${dir}/exp/tri3b || exit 1;
fi

# Decode triphone models
if [ ${stage} -le 3 ]; then
  utils/mkgraph.sh ${REC_ROOT}/data/lang_largevocab_test ${dir}/exp/tri3b ${dir}/exp/tri3b/graph_largevocab || exit 1;

  steps/decode_fmllr.sh --nj ${decode_nj} --cmd "$decode_cmd" \
    --num-threads 4 --parallel-opts "${parallel_opts}" \
    --scoring-opts "--min-lmwt 0 --max-lmwt 0" \
    ${dir}/exp/tri3b/graph_largevocab ${dir}/test ${dir}/exp/tri3b/decode_largevocab_test || exit 1

  utils/mkgraph.sh ${REC_ROOT}/data/lang_largevocab_test ${dir}/exp/tri3b ${dir}/exp/tri3b/graph_largevocab || exit 1;

  steps/decode_fmllr.sh --nj ${decode_nj} --cmd "$decode_cmd" \
    --num-threads 4 --parallel-opts "${parallel_opts}" \
    --scoring-opts "--min-lmwt 0 --max-lmwt 0" \
    ${dir}/exp/tri3b/graph_largevocab ${dir}/test ${dir}/exp/tri3b/decode_largevocab_test || exit 1
fi
