#!/usr/bin/env python

"""show_mlf.py

Shows the MLF endpoints from the uaspeech.endpoints.mlf file in conf/.
"""

from __future__ import print_function, unicode_literals

import json
import logging
import os
import random
import scipy
import scipy.io.wavfile as wavefile
import matplotlib.pyplot as pplot
import sys
import re

__author__ = 'rmarxer'


FILENAME_RE = re.compile(r'(?:^\"(?P<file>.*?)\"$)')   # The file name of the MLF


def run_length_encoding(x):
    pos, = scipy.where(scipy.diff(x) != 0)
    pos = scipy.concatenate(([0], pos+1, [len(x)]))
    rle = [(a, b, x[a]) for (a, b) in zip(pos[:-1], pos[1:])]
    return rle


def str_to_mask(strng):
    return scipy.array(map(int, strng.replace('[', '').replace(']', '').split()))


def translate_filename(filename, uaspeech_uttids):
    fnm, ext = os.path.splitext(os.path.basename(filename))

    uttid = fnm.split('_')[1]

    if uttid not in uaspeech_uttids:
        logging.warning('Could not find the utterance-id of {}. Skipping it...'.format(uttid))
        return None

    return uaspeech_uttids[uttid]


def load_mlf(mlf_filename, uaspeech_uttids):
    print('Loading {} ...'.format(mlf_filename))
    vad = {}

    current_filename = None
    with open(mlf_filename) as f:
        for line in f:
            matches = FILENAME_RE.findall(line)
            if matches:
                current_filename = translate_filename(matches[0], uaspeech_uttids)

            else:
                tokens = line.strip().split(' ')
                start = int(tokens[0])
                end = int(tokens[1])

                symb = tokens[2]

                word = tokens[3] if len(tokens) > 3 else ''

                if current_filename is not None:
                    vad.setdefault(current_filename, []).append({'start': start,
                                                                 'end': end,
                                                                 'symbol': symb,
                                                                 'word': word})

    return vad


def show_mlf(utt_id, mlf):
    print('Showing {} ...'.format(utt_id))
    speaker, block, word, mic = utt_id.split('_')

    wav_filename = '/Users/rmarxer/data/UASPEECH/audio/{}{}/{}.wav'.format('control/'
                                                                           if speaker.startswith('C')
                                                                           else '',
                                                                           speaker,
                                                                           utt_id)

    print('Loading WAV {} ...'.format(wav_filename))
    rate, wav = wavefile.read(wav_filename)

    t = scipy.arange(len(wav)) / float(rate)
    pplot.plot(t, wav)

    mlf_rate = 10000000

    for segment in mlf[utt_id]:
        start = segment['start']
        end = segment['end']

        word = segment['word']

        pplot.axvspan(start/float(mlf_rate), end/float(mlf_rate),
                      color='g' if word == '!SENT_START' else 'r', alpha=0.5)

    pplot.show()


def main():
    mlf_filename = 'conf/christensen_endpoints.mlf'
    utt_id = None

    if len(sys.argv) > 1:
        mlf_filename = sys.argv[1]

    if len(sys.argv) > 2:
        utt_id = sys.argv[2]

    with open('results/tmp/uaspeech.json') as f:
        uaspeech = json.load(f)

    uaspeech_uttids = {k.replace('_', ''): k for k in uaspeech['utterances']}

    vad = load_mlf(mlf_filename, uaspeech_uttids)

    if not utt_id:
        utt_id = vad.keys()[int(random.random()*len(vad))]

    show_mlf(utt_id, vad)


if __name__ == '__main__':
    main()
