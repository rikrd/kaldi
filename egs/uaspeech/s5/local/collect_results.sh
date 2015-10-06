#!/usr/bin/env bash
# Copyright 2015  University of Sheffield (Author: Ricard Marxer)
# Apache 2.0


find . -iname "test_filt.txt" \
| xargs jq -R -f local/collect_results.jq