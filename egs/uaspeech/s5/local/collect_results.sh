#!/usr/bin/env bash
# Copyright 2015  University of Sheffield (Author: Ricard Marxer)
# Apache 2.0

# Convert the transcriptions from integers to words
for transcription in `find . -iname "*.tra"`; do
    transcription_dir=`dirname ${transcription}`
    words_dir=`dirname ${transcription_dir} | sed 's/decode_/graph_/' | sed 's/_test//' | sed 's/\.si//'`
    utils/int2sym.pl -f 2- ${words_dir}/words.txt ${transcription} > ${transcription}.sym
done

# Collect into one JSON all the transcriptions (and reference text) of the utterances
find . -iname "*.tra.sym" -o -iname "test_filt.txt" \
    | xargs jq -R -f local/collect_transcriptions.jq > results.json



# Summarize
jq -f local/summarize.jq results.json