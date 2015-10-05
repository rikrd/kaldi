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

mkdir -p ${REC_ROOT}

local/run_init.sh \
    --overwrite "${overwrite}" --stage "${stage}" \
    --feature "${feature}" --feature-maker "${feature_maker}"

local/run_leave_out.sh \
    --overwrite "${overwrite}" --stage "${stage}" \
    --feature "${feature}" \
    --max-count "${max_count}"

for dir in `ls ${REC_ROOT}/leave_one_out`; do
    qsub -l mem=24G,rmem=20G,h_rt=48:00:00 -j y -o ${logfile} local/run_gmm.sh --stage "${stage}" --overwrite "${overwrite}" ${dir}
done
