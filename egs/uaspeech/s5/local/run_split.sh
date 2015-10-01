#!/usr/bin/env bash
#
# UASPEECH Database of Dysarthric Articulation
# http://www.isle.illinois.edu/sst/data/UASpeech/
#
# Split the data into train, adapt and test given two jq filters
#
# Copyright  2015 University of Sheffield (Author: Ricard Marxer)
#
# Apache 2.0
#

script_path=`dirname $0`

. ${script_path}/../cmd.sh
. ${script_path}/../path.sh

feature=mfcc
jq_args=

. ${script_path}/../utils/parse_options.sh # accept options

if [ $# -ne 4 ]; then
  printf "\nUSAGE: %s <train filter> <test filter> <adapt filter> <directory>\n\n" `basename $0`
  echo "The argument specifies the input and output directory that "
  echo "should contain 'train', 'adapt' and 'test' data dirs in Kaldi format"
  exit 1;
fi

train_filter=$1
adapt_filter=$2
test_filter=$3
dir=$4

mkdir -p $dir

${jq_cmd} ${jq_args} -r "${train_filter}" ${REC_ROOT}/tmp/uaspeech.json > ${dir}/train_filter
${jq_cmd} ${jq_args} -r "${adapt_filter}" ${REC_ROOT}/tmp/uaspeech.json > ${dir}/adapt_filter
${jq_cmd} ${jq_args} -r "${test_filter}" ${REC_ROOT}/tmp/uaspeech.json > ${dir}/test_filter

src_dir=${REC_ROOT}/data/${feature}_data_full

. ${script_path}/../local/reduce_data_dir_by_reclist.sh ${src_dir} ${dir}/train_filter ${dir}/train
. ${script_path}/../local/reduce_data_dir_by_reclist.sh ${src_dir} ${dir}/adapt_filter ${dir}/adapt
. ${script_path}/../local/reduce_data_dir_by_reclist.sh ${src_dir} ${dir}/test_filter ${dir}/test
