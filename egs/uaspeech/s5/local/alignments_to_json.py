#!/usr/bin/env python

"""alignments_to_json.py

Write to JSON the alignment result from a alignment ark file produced by Kaldi.

Uses the following command to get the alignment:
ali-to-phones --ctm-output my.mdl ark,t:"gunzip -c ali.1.gz|" - | utils/int2sym.pl -f 5 phones.txt -

Usage:
alignments_to_json.py [options] <alignment_file> <lang_directory> [<utterance_id>]
alignments_to_json.py --help

Options:
<alignment_file>          path to alignment file
<lang_directory>          path to alignment file
<utternace_id>            file containing the possible words of the language
--help, -h                display this help screen
"""


from __future__ import print_function, unicode_literals
import os
import json
import random
import subprocess
import docopt

__author__ = 'rmarxer'


def make_regions(segments):
    # Prepare the segments for the wavesurfer regions plugin
    segments_clean = [(start, end, label.replace('_B', '').replace('_E', '').replace('_I', '').replace('_S', ''))
                      for start, end, label in segments
                      if label != 'SIL']

    regions = []
    for start, end, label in segments_clean:
        rgba = 'rgba({},{},{}, 0.3)'.format(random.randint(0, 255),
                                            random.randint(0, 255),
                                            random.randint(0, 255))

        regions.append({'start': start,
                        'end': end,
                        'color': rgba,
                        'attributes': {
                            'label': label
                        }
                        })
    return regions


def load_alignments(alignment_filename, lang_directory):
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

    results = []
    for utt_id, segments in alignments.iteritems():
        speaker, block, word, mic = utt_id.split('_')

        wav_filename = '/Users/rmarxer/data/UASPEECH/audio/{}{}/{}.wav'.format('control/'
                                                                               if speaker.startswith('C')
                                                                               else '',
                                                                               speaker,
                                                                               utt_id)

        wav_filename = os.path.relpath(wav_filename, os.path.expanduser('~'))

        results.append({'utterance_id': utt_id,
                        'regions': make_regions(segments),
                        'wav_filename': wav_filename})

    return results


def main():
    args = docopt.docopt(__doc__)

    alignments = load_alignments(args['<alignment_file>'], args['<lang_directory>'])

    print(json.dumps(alignments, indent=4))

if __name__ == '__main__':
    main()
