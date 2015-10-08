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

mkdir -p ${REC_ROOT}/data

${jq_cmd} -r '.utterances | to_entries | map(.value.audio_prompt) | unique | .[]' \
    ${REC_ROOT}/tmp/uaspeech.json > ${REC_ROOT}/tmp/uaspeech_words.txt || exit 1

local/prepare_lm_anyword.py ${REC_ROOT}/data/lang ${REC_ROOT}/tmp/uaspeech_words.txt \
    ${REC_ROOT}/data/lang_uaspeechvocab_test || exit 1
