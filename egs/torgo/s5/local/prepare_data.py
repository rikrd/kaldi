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
import logging
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
    return x


def validate_kaldi_data(data_dirs, options=''):
    for data_dir in data_dirs:
        cmd = 'utils/validate_data_dir.sh {options} {data_dir}'.format(data_dir=data_dir,
                                                                       options=options)
        logging.info(cmd)
        subprocess.call(cmd, shell=True)


def torgo_to_kaldi(utterance):
    """Takes as input a utterance from the TORGO dataset and returns a utterance for the Kaldi scripts:

    uttid - utterance ID
    transcription - word transcription of the utterance
    speaker - speaker ID
    audio_filename - absolute path to the audio filename
    start_time - [optional] start time in seconds of the utterance in the audio file (if not present 0 is assumed)
    end_time - [optional] end time in seconds of the utterance in the audio file (if not present the length of the file
                            is assumed)
    gender - [optional] M if male F if female


    :param utterance:
    :return:
    """
    utt_id, utt = utterance

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

    utt.update({'transcription': transcription})

    return utt_id, utt


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
        write_sorted(base_path, 'text', '{utterance_id} {transcription}', utterance_set)

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


def split_train_test_dev(utterances, train_count=0.8, test_count=0.1, dev_count=0.1):
    randomized = copy.deepcopy(utterances.keys())
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

    # Blacklist of utterances (corrupted audios, transcriptions etc...)
    def accept_utterance(utterance_item):
        utt_id, utt = utterance_item

        return (
            utt['stimuli']
            and utt['stimuli']['type'] == 'prompt'
            and utt['audio_filename']
            and utt['sensor'] == 'headMic'
            and os.path.isfile(utt['audio_filename'])
            and os.path.getsize(utt['audio_filename']) > 1000  # filter audio files under 1kb
        )

    # Filter utterance, keep only those with prompted stimuli
    utterances_filtered = filter(accept_utterance,
                                 dataset['utterances'].items())

    dataset['utterances'] = dict(map(torgo_to_kaldi, utterances_filtered))

    # Split the dataset in train, dev and test
    utterance_sets = split_train_test_dev(dataset['utterances'])

    # Create the data files needed by kaldi (text, utt2spk, segments, ...)
    data_dirs = prepare_kaldi_data(dataset, utterance_sets, output_root)

    # Validata the data files
    validate_kaldi_data(data_dirs, options='--no-feats')

    return

if __name__ == '__main__':
    main()