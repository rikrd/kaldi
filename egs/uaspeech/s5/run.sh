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

stage=0
overwrite=false

feature=mfcc
feature_maker=steps/make_mfcc.sh
max_count=

. utils/parse_options.sh # accept options

local/run_all.sh --feature "${feature}" --feature_maker "${feature_maker}" \
    --max-count "${max_count}" --stage "${stage}" --overwrite "${overwrite}" \
    --setting "adapt_to_one"

local/run_all.sh --feature "${feature}" --feature_maker "${feature_maker}" \
    --max-count "${max_count}" --stage "${stage}" --overwrite "${overwrite}" \
    --setting "leave_out"
