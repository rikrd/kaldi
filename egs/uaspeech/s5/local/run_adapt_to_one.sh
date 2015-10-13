#!/usr/bin/env bash
#
# UASPEECH Database of Dysarthric Articulation
# http://www.isle.illinois.edu/sst/data/UASpeech/
#
# Copyright  2015 University of Sheffield (Author: Ricard Marxer)
#
# Apache 2.0
#

script_path=`dirname $0`

. ${script_path}/../cmd.sh
. ${script_path}/../path.sh

overwrite=false
feature=mfcc
max_count=
stage=0

. ${script_path}/../utils/parse_options.sh # accept options

mkdir -p ${REC_ROOT}/adapt_to_one

if [ ${stage} -le 10 ]; then
    dysarthric_speakers=`${jq_cmd} -r '.speakers | with_entries(select(.value.type!="control")) | keys[]' ${REC_ROOT}/tmp/uaspeech.json`

    for speaker in ${dysarthric_speakers}; do
        echo "Processing speaker ${speaker} ..."
        local/split_data_with_jq.sh --max-count "${max_count}" --feature ${feature} --jq-args "--arg speaker ${speaker}" \
          '.speakers as $speakers | .utterances[] | select($speakers[.speaker].type!="control" and ((.speaker==$speaker and .block=="2") | not)) | .utterance_id' \
          '.speakers as $speakers | .utterances[] | select($speakers[.speaker].type!="control" and .speaker==$speaker and .block!="2") | .utterance_id' \
          '.speakers as $speakers | .utterances[] | select($speakers[.speaker].type!="control" and .speaker==$speaker and .block=="2") | .utterance_id' \
           ${REC_ROOT}/adapt_to_one/${speaker}
    done
fi