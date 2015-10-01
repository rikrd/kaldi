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
prepare_data.py <data_json> <output_root>
prepare_data.py --help

Options:
<data_json>                path to the DATA JSON file
<output_root>               output directory root
--help, -h                  display this help screen
"""

from __future__ import print_function, unicode_literals
import copy
import json
import logging
import os
import random
import locale
import subprocess
from inspect import isfunction

import docopt

__author__ = 'rmarxer'


def c_sort(x):
    locale.setlocale(locale.LC_ALL, ('C', ''))
    x.sort(cmp=locale.strcoll)
    return x


def validate_kaldi_data(data_dirs, options=''):
    for data_dir in data_dirs:
        cmd = 'utils/validate_data_dir.sh {options} {data_dir}'.format(data_dir=data_dir,
                                                                       options=options)
        logging.info(cmd)
        subprocess.call(cmd, shell=True)


def write_sorted(directory, filename, format_pattern, utterance_set):
    lines = [format_pattern.format(**utt)
             for utt in utterance_set]
    lines = c_sort(lines)

    with open(os.path.join(directory, filename), 'w') as f:
        f.writelines(['{}\n'.format(line) for line in lines])


def prepare_kaldi_data(dataset, utterance_sets, output_root):
    data_dirs = []

    speaker_set = dataset['speakers']

    for name, utterances in utterance_sets.items():
        base_path = os.path.join(output_root, 'data', name)

        if not os.path.isdir(base_path):
            os.makedirs(base_path)

        utterance_set = [dataset['utterances'][utterance] for utterance in utterances]

        # Create text file (<utterance-id> <transcription>)
        # TODO: Allow adding a transcription prefix and suffix (e.g. padding with '<UNK>' for non endpointed data)
        write_sorted(base_path, 'text', '{utterance_id} {audio_transcription}', utterance_set)

        # Create wav.scp file (<recording-id> <audio-extended-filename>)
        write_sorted(base_path, 'wav.scp', '{recording_id} {audio_rspecifier}', utterance_set)

        # Create segments file (<utt-id> <rec-id> <start_time> <end_time>)
        if any([utt.get('start_time', None) for utt in utterance_set]) \
                or any([utt.get('end_time', None) for utt in utterance_set]):
            write_sorted(base_path, 'segments', '{utterance_id} {recording_id} {start_time} {end_time}', utterance_set)

        # Create reco2file_channel file (<recording-id> <filename> <recording-side (A or B)>)
        # TODO: implement this if needed

        # Create utt2spk file (<utterance-id> <speaker-id>)
        write_sorted(base_path, 'utt2spk', '{utterance_id} {speaker}', utterance_set)

        # Create spk2gender file (<speaker-id> <gender (m or f)>)
        write_sorted(base_path, 'spk2gender', '{speaker} {gender}',
                     [{'speaker': speaker, 'gender': speaker_set[speaker]['gender']}
                      for speaker in {utt['speaker'] for utt in utterance_set}])

        # Create spk2utt file (<speaker-id> <utterance-id-1> <utterance-id-2> <utterance-id-3> ...)
        write_sorted(base_path, 'spk2utt', '{speaker} {uttids}',
                     [{'speaker': speaker, 'uttids': ' '.join(c_sort([utt['utterance_id']
                                                                      for utt in utterance_set
                                                                      if utt['speaker'] == speaker]))}
                      for speaker in {utt['speaker'] for utt in utterance_set}])

        data_dirs.append(base_path)

    return data_dirs


def split_train_test(utterances,
                     train_selection=lambda x: x['block'] in {'1', '2'},
                     test_selection=lambda x: x['block'] in {'3'}):

    if isinstance(train_selection, float) and isinstance(test_selection, float):
        randomized = copy.deepcopy(utterances.keys())
        random.shuffle(randomized)

        count = len(randomized)
        train_count, test_count = (int(count*train_selection),
                                   int(count*test_selection))

        return {'train': randomized[:train_count],
                'test': randomized[train_count:train_count+test_count]}

    elif isfunction(train_selection) and isfunction(test_selection):
        return {'train': [utt_id for utt_id, utt in utterances.iteritems() if train_selection(utt)],
                'test': [utt_id for utt_id, utt in utterances.iteritems() if test_selection(utt)]}

    raise ValueError('train_selection and test_selection keyword arguments '
                     'must be of same type and can only be floats or functions.')


def main():
    args = docopt.docopt(__doc__)

    output_root = args['<output_root>']

    with open(args['<data_json>']) as f:
        dataset = json.load(f)

    utterance_sets = {'mfcc_data_full': [utt_id for utt_id in dataset['utterances'].iterkeys()]}

    # Create the data files needed by kaldi (text, utt2spk, segments, ...)
    data_dirs = prepare_kaldi_data(dataset, utterance_sets, output_root)

    # Validata the data files
    validate_kaldi_data(data_dirs, options='--no-feats')

    return

if __name__ == '__main__':
    main()