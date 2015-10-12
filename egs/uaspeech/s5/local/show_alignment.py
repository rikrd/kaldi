#!/usr/bin/env python

"""show_alignment.py

Shows the alignment result from a alignment ark file produced by Kaldi.

Uses the following command to get the alignment:
ali-to-phones --ctm-output my.mdl ark,t:"gunzip -c ali.1.gz|" - | utils/int2sym.pl -f 5 phones.txt -

Usage:
show_alignment.py [options] <alignment_file> <lang_directory> [<utterance_id>]
show_alignment.py --help

Options:
<alignment_file>          path to alignment file
<lang_directory>          path to alignment file
<utternace_id>            file containing the possible words of the language
--help, -h                display this help screen
"""


from __future__ import print_function, unicode_literals
import os
import random
import subprocess
import scipy
import scipy.io.wavfile as wavefile
import matplotlib.pyplot as pplot
import docopt

__author__ = 'rmarxer'


def load_alignments(alignment_filename, lang_directory):
    print('Loading {} ...'.format(alignment_filename))

    model_filename = os.path.join(os.path.dirname(alignment_filename), 'final.mdl')

    lines = subprocess.check_output('ali-to-phones --print-args=false --ctm-output {} ark,t:"gunzip -c {}|" - '
                                    '| utils/int2sym.pl -f 5 {} -'.format(model_filename,
                                                                          alignment_filename,
                                                                          os.path.join(lang_directory,
                                                                                       'phones.txt')),
                                    stderr=None,
                                    shell=True)

    # CTM format e.g. F02_B1_C11_M2 1 0.00 4.53 SIL
    alignments = {}
    for l in lines.split('\n'):
        if not l.strip():
            continue

        utt_id, _, start, length, label = l.strip().split(' ')

        alignments.setdefault(utt_id, []).append((float(start), float(start)+float(length), label))

    return alignments


def show_alignment(utt_id, alignments):
    print('Showing {} ...'.format(utt_id))
    speaker, block, word, mic = utt_id.split('_')

    wav_filename = '/Users/rmarxer/data/UASPEECH/audio/{}{}/{}.wav'.format('control/' if speaker.startswith('C') else '',
                                                                           speaker,
                                                                           utt_id)

    print('Loading WAV {} ...'.format(wav_filename))
    rate, wav = wavefile.read(wav_filename)

    t = scipy.arange(len(wav)) / float(rate)

    pplot.plot(t, wav)
    segments = alignments[utt_id]
    print(segments)
    for start, end, label in segments:
        if label == 'SIL':
            continue

        length = end-start
        pplot.axvspan(start, end, color='g', alpha=0.5)
        pplot.annotate(label.replace('_B', '').replace('_E', '').replace('_I', '').replace('_S', ''),
                       xy=(start + length/2.0, 1), xytext=(start + length/2.0, 1.5), textcoords='data')

    pplot.show()


def main():
    args = docopt.docopt(__doc__)

    utt_id = None

    alignments = load_alignments(args['<alignment_file>'], args['<lang_directory>'])

    if not utt_id:
        utt_id = alignments.keys()[int(random.random()*len(alignments))]

    show_alignment(utt_id, alignments)


if __name__ == '__main__':
    main()
