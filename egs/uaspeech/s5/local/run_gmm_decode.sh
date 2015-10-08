#!/usr/bin/env bash
#
# UASPEECH Database of Dysarthric Articulation
# http://www.isle.illinois.edu/sst/data/UASpeech/
#
# Perform a task using the GMM models
#
# Copyright  2015 University of Sheffield (Author: Ricard Marxer)
#
# Apache 2.0
#

script_path=`dirname $0`

. ${script_path}/../cmd.sh
. ${script_path}/../path.sh

nj=12
align_nj=1
decode_nj=1
parallel_opts=

stage=0
overwrite=false

. ${script_path}/../utils/parse_options.sh # accept options

if [ $# -ne 2 ]; then
  printf "\nUSAGE: %s <task> <directory>\n\n" `basename $0`
  echo "The <directory> argument specifies the input and output directory that "
  echo "should contain 'train' and 'test' data dirs in Kaldi format."
  echo "The <task> argument specifies the task. The directory local/make_task_${task}.sh should exist"
  exit 1;
fi

dir=$1
task=$2

# Make the task (creates ${REC_ROOT}/data/lang_${task}_test)
local/make_task_${task}.sh

# Decode monophone model
if [ ${stage} -le 25 ]; then
  utils/mkgraph.sh ${REC_ROOT}/data/lang_${task}_test ${dir}/exp/tri1 ${dir}/exp/tri1/graph_${task} || exit 1;

  steps/decode.sh --nj ${decode_nj} --cmd "$decode_cmd" \
    --num-threads 4 --parallel-opts "${parallel_opts}" \
    --scoring-opts "--min-lmwt 1 --max-lmwt 1" \
    ${dir}/exp/tri1/graph_${task} ${dir}/test ${dir}/exp/tri1/decode_${task}_test || exit 1;
fi

# Decode triphone models
if [ ${stage} -le 26 ]; then
  utils/mkgraph.sh ${REC_ROOT}/data/lang_${task}_test ${dir}/exp/tri2b ${dir}/exp/tri2b/graph_${task} || exit 1;

  steps/decode_fmllr.sh --nj ${decode_nj} --cmd "$decode_cmd" \
    --num-threads 4 --parallel-opts "${parallel_opts}" \
    --scoring-opts "--min-lmwt 1 --max-lmwt 1" \
    ${dir}/exp/tri2b/graph_${task} ${dir}/test ${dir}/exp/tri2b/decode_${task}_test || exit 1;

  utils/mkgraph.sh ${REC_ROOT}/data/lang_${task}_test ${dir}/exp/tri3b ${dir}/exp/tri3b/graph_${task} || exit 1;

  steps/decode_fmllr.sh --nj ${decode_nj} --cmd "$decode_cmd" \
    --num-threads 4 --parallel-opts "${parallel_opts}" \
    --scoring-opts "--min-lmwt 1 --max-lmwt 1" \
    ${dir}/exp/tri3b/graph_${task} ${dir}/test ${dir}/exp/tri3b/decode_${task}_test || exit 1;
fi

# Decode the adapted models
if [ ${stage} -le 27 ]; then
  utils/mkgraph.sh \
    ${REC_ROOT}/data/lang_${task}_test ${dir}/exp/tri3b_adapt ${dir}/exp/tri3b_adapt/graph_${task} || exit 1;

  steps/decode_fmllr.sh --nj ${decode_nj} --cmd "$decode_cmd" \
    --num-threads 4 --parallel-opts "${parallel_opts}" \
    --scoring-opts "--min-lmwt 1 --max-lmwt 1" \
    ${dir}/exp/tri3b_adapt/graph_${task} ${dir}/test ${dir}/exp/tri3b_adapt/decode_${task}_test || exit 1;
fi
