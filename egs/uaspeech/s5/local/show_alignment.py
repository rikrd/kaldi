#!/usr/bin/env python

"""show_alignment.py

Shows the alignment result from a alignment ark file produced by Kaldi.
"""

from __future__ import print_function, unicode_literals
import random
import scipy
import scipy.io.wavfile as wavefile
import matplotlib.pyplot as pplot
import sys

__author__ = 'rmarxer'


def run_length_encoding(x):
    pos, = scipy.where(scipy.diff(x) != 0)
    pos = scipy.concatenate(([0], pos+1, [len(x)]))
    rle = [(a, b, x[a]) for (a, b) in zip(pos[:-1], pos[1:])]
    return rle


def str_to_mask(strng):
    return scipy.array(map(int, strng.replace('[', '').replace(']', '').split()))


def load_alignment(vad_filename):
    print('Loading {} ...'.format(vad_filename))
    vad = {}
    with open(vad_filename) as f:
        lines = f.readlines()
        for l in lines:
            utt_id, mask = l.strip().split(' ', 1)

            if not utt_id.endswith('2'):
                continue

            vad[utt_id] = mask

    return vad


def show_alignment(utt_id, vad):
    print('Showing {} ...'.format(utt_id))
    speaker, block, word, mic = utt_id.split('_')

    wav_filename = '/Users/rmarxer/data/UASPEECH/audio/{}{}/{}.wav'.format('control/' if speaker.startswith('C') else '',
                                                                           speaker,
                                                                           utt_id)

    print('Loading WAV {} ...'.format(wav_filename))
    rate, wav = wavefile.read(wav_filename)
    mask = str_to_mask(vad[utt_id])

    mask_rate = 1000./10.

    t = scipy.arange(len(wav)) / float(rate)
    t_mask = scipy.arange(len(mask)) / float(mask_rate)

    pplot.plot(t, wav)

    runs = run_length_encoding(mask)

    for start, end, value in runs:
        if not value == 1:
            continue

        pplot.axvspan(t_mask[start], t_mask[end], color='g', alpha=0.5)

    pplot.show()


def main():
    vad_filename = 'vad.ark'
    utt_id = None

    if len(sys.argv) > 1:
        vad_filename = sys.argv[1]

    if len(sys.argv) > 2:
        utt_id = sys.argv[2]

    vad = load_alignment(vad_filename)

    if not utt_id:
        utt_id = vad.keys()[int(random.random()*len(vad))]

    show_alignment(utt_id, vad)


if __name__ == '__main__':
    main()
