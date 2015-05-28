#!/usr/bin/env bash

# "queue.pl" uses qsub.  The options to it are
# options to qsub.  If you have GridEngine installed,
# change this to a queue you have access to.
# Otherwise, use "run.pl", which will run jobs locally
# (make sure your --num-jobs options are no more than
# the number of cpus on your machine.

# Run locally:
export train_cmd="run.pl"
export decode_cmd="run.pl"
export cuda_cmd="run.pl"
export parallel_opts=""

host=`hostname -f`

# If on the Iceberg cluster...
if [ ${host#*.} == "iceberg.shef.ac.uk" ]; then
  export train_cmd="queue.pl"
  export decode_cmd="queue.pl"
  export cuda_cmd="queue.pl --gpu=1"
  export parallel_opts="-pe openmp 4"
fi
