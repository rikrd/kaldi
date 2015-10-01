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

for speaker in `${jq_cmd} -r '.speakers | with_entries(select(.value.type!="control")) | keys[]' ${REC_ROOT}/tmp/uaspeech.json`; do
    echo "Processing speaker $speaker ..."
    local/run_split.sh --feature $feature --jq-args "--arg speaker $speaker" \
      '.speakers as $speakers | .utterances[] | select($speakers[.speaker].type!="control" and .speaker!=$speaker) | .utterance_id' \
      '.speakers as $speakers | .utterances[] | select($speakers[.speaker].type!="control" and .speaker==$speaker and .block!="2") | .utterance_id' \
      '.speakers as $speakers | .utterances[] | select($speakers[.speaker].type!="control" and .speaker==$speaker and .block=="2") | .utterance_id' \
       ${REC_ROOT}/leave_one_out_$speaker
done
