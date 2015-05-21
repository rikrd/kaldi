#!/usr/bin/env python

"""prepare_data.py

Prepares the data files necessary for Kaldi training using as input the JSON file.

The files it creates are [starred are optional]:
text
wav.scp
segments*
reco2file_and_channel*
utt2spk
spk2gender*


Usage:
prepare_data.py <torgo_json> <output_root>
prepare_data.py --help

Options:
<torgo_json>                path to the TORGO JSON file
<output_root>               output directory root
--help, -h                  display this help screen
"""

from __future__ import print_function, unicode_literals
import copy
import json
import os
import random
import locale
import subprocess

import docopt
import re

__author__ = 'rmarxer'


def c_sort(x):
    locale.setlocale(locale.LC_ALL, ('C', ''))
    x.sort(cmp=locale.strcoll)


def validate_kaldi_data(data_dirs):
    for data_dir in data_dirs:
        subprocess.call('utils/validate_data_dir.sh --no-feats {}'.format(data_dir))


def torgo_to_kaldi(utt):
    """Takes as input a utterance from the TORGO dataset and returns a utterance for the Kaldi scripts:

    uttid - utterance ID
    transcription - word transcription of the utterance
    speaker - speaker ID
    audio_filename - absolute path to the audio filename
    start_time - [optional] start time in seconds of the utterance in the audio file (if not present 0 is assumed)
    end_time - [optional] end time in seconds of the utterance in the audio file (if not present the length of the file
                            is assumed)
    gender - [optional] M if male F if female


    :param utt:
    :return:
    """
    prompt = utt['stimuli']['prompt']

    transcription = prompt

    # Remove \r
    transcription = re.sub(r'\r', r'', transcription)

    # Remove instructions
    transcription = re.sub(r'(\[.*\])', r'', transcription)

    # Remove , ? ! ;
    transcription = re.sub(r'([,!?;])', r'', transcription)

    # Remove . only when before space or at end
    transcription = re.sub(r'(\.)($| )', r'', transcription)

    transcription = transcription.upper()

    return {'uttid': '{speaker}_{session}_{id}'.format(**utt),
            'transcription': transcription,
            'speaker': '{speaker}'.format(**utt),
            'gender': utt['speaker'][0],
            'audio_filename': utt['audio_filename']}


def prepare_kaldi_data(utterance_sets, output_root):
    data_dirs = []

    for name, utterance_set in utterance_sets.items():
        output_dir = os.path.join(output_root, name)

        if not os.path.isdir(output_dir):
            os.makedirs(output_dir)

        # Create text file (<utt-id> <transcription>)
        text_lines = ['{uttid} {transcription}'.format(**utt)
                      for utt in utterance_set]

        c_sort(text_lines)

        data_dirs.append(output_dir)

    return data_dirs


def split_train_test_dev(utterances, train_count=0.8, test_count=0.1, dev_count=0.1):
    randomized = copy.deepcopy(utterances)
    random.shuffle(randomized)

    count = len(randomized)

    train_count, test_count, dev_count = (int(count*train_count),
                                          int(count*test_count),
                                          int(count*dev_count))

    return {'train': randomized[:train_count],
            'test': randomized[train_count:train_count+test_count],
            'dev': randomized[train_count+test_count:train_count+test_count+dev_count]}


def main():
    args = docopt.docopt(__doc__)

    output_root = args['<output_root>']

    with open(args['<torgo_json>']) as f:
        dataset = json.load(f)

    # Filter utterance, keep only those with prompted stimuli
    utterances_filtered = filter(lambda utt: (utt['stimuli']
                                              and utt['stimuli']['type'] == 'prompt'
                                              and utt['audio_filename']),
                                 dataset['utterances'])

    utterances_kaldi = map(torgo_to_kaldi, utterances_filtered)

    # Split the dataset in train, dev and test
    utterance_sets = split_train_test_dev(utterances_kaldi)

    # Create the data files needed by kaldi (text, utt2spk, segments, ...)
    data_dirs = prepare_kaldi_data(utterance_sets, output_root)

    # Validata the data files
    validate_kaldi_data(data_dirs)

    return

if __name__ == '__main__':
    main()