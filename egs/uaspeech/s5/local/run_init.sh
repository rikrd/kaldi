#!/usr/bin/env bash
#
# UASPEECH Database of Dysarthric Articulation
# http://www.isle.illinois.edu/sst/data/UASpeech/
#
# Parses the UASPEECH database into a JSON file
# Prepares the data directory following Kaldi's convention
# Prepares the lang directory following Kaldi's convention
# Prepares a large vocabulary task
#
# Copyright  2015 University of Sheffield (Author: Ricard Marxer)
#
# Apache 2.0
#

script_path=`dirname $0`

. ${script_path}/../cmd.sh
. ${script_path}/../path.sh

nj=12
decode_nj=16
parallel_opts=

stage=0
overwrite=false
feature=mfcc
feature_maker=steps/make_mfcc.sh

. ${script_path}/../utils/parse_options.sh # accept options

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
feat_dir=${REC_ROOT}/data/${feature}_features
if [ ${stage} -le 1 ]; then
  dir=${REC_ROOT}/data/${feature}_data_full

  if [ ! -d "${dir}" ] || [ "$overwrite" = true ]; then
    ${feature_maker} --nj $nj --cmd "$train_cmd" $dir $dir/log $dir/data || exit 1

    steps/compute_cmvn_stats.sh $dir $dir/log $dir/data || exit 1

    utils/fix_data_dir.sh $dir || exit 1
  fi
fi
