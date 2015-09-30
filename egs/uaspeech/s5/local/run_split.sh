#!/usr/bin/env bash
#
# UASPEECH Database of Dysarthric Articulation
# http://www.isle.illinois.edu/sst/data/UASpeech/
#
# Split the data into train and test given two jq filters
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

if [ $# -ne 1 ]; then
  printf "\nUSAGE: %s <train filter> <test filter> <directory>\n\n" `basename $0`
  echo "The argument specifies the input and output directory that "
  echo "should contain 'train' and 'test' data dirs in Kaldi format"
  exit 1;
fi

dir=$1

