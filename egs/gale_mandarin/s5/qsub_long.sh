#!/usr/bin/env bash

for scriptname in "$@"
do
    filename=$(basename "$scriptname")
    filename="${filename%.*}"

    logfile=~/log_gale_mandarin_${filename}.txt

    qsub -l mem=24G,rmem=20G,h_rt=48:00:00 -j y -o ${logfile} ${scriptname}
done

