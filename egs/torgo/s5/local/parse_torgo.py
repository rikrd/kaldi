#!/usr/bin/env python
"""parse_torgo.py

Parses the TORGO database into a JSON file

Usage:
parse_torgo.py [options] <torgo_path> <output_json_path>
parse_torgo.py --help

Options:
<torgo_path>                path to the TORGO dataset
<output_json_path>          path to the JSON file
--overwrite, -o             overwrite the JSON file if it exists
--help, -h                  display this help screen
"""

from __future__ import print_function, unicode_literals
import codecs
import fnmatch
import json
import logging
import os
import wave
import re

import docopt

__author__ = 'rmarxer'

# Pattern to match paths such as:
# /path/to/TORGO/F04/Session2/phn_headMic/0098.phn
torgo_phn_pattern = r'.*/(?P<speaker>.*)/Session(?P<session>.*)/phn_(?P<sensor>.*)/(?P<id>\d+)( (.*))*\.phn'


def clean_prompt(prompt):
    return prompt \
        .replace(', ', ' ') \
        .replace('.\n', '') \
        .strip()


def get_audio_info(audio_filename):
    with open(audio_filename, 'rb') as file_object:
        wav_object = wave.open(file_object, 'r')
        sample_rate = wav_object.getframerate()
        audio_info = {'audio_sample_rate': sample_rate,
                      'audio_length': wav_object.getnframes() / float(sample_rate)}

    return audio_info


def load_transcription(filename, audio_length=None):
    transcription = []

    # FIXED Some transcription files are in 16.0kHz others in 44.1kHz
    # e.g. /Users/rmarxer/data/TORGO/M01/Session2_3/phn_arrayMic/0080.PHN   ->   44.1 kHz
    # e.g. /Users/rmarxer/data/TORGO/F03/Session2/phn_headMic/0133.phn      ->   16.0 kHz
    with codecs.open(filename, 'r', 'utf-8') as f:
        for line in f:
            start, end, symbol = line.strip().split(' ', 3)

            transcription.append({'start_time': float(start),
                                  'end_time': float(end),
                                  'symbol': symbol})

    # Try to guess the sample rate from the audio_length
    sample_rate = 16000.0
    if audio_length is not None:
        if transcription:
            max_end_time = max(v['end_time'] for v in transcription)
            approx_sample_rate = (max_end_time / audio_length)

            sample_rates = [16000, 22500, 44100, 48000]

            sample_rate = min(sample_rates, key=lambda x: abs(x-approx_sample_rate))

    # Convert the transcription times from samples to seconds
    for item in transcription:
        item['start_time'] /= sample_rate
        item['end_time'] /= sample_rate

    return transcription


def parse_stimuli(stimuli):
    if stimuli.endswith('.jpg') or stimuli.endswith('.png'):
        return {'type': 'image_description',
                'image_filename': stimuli}

    match = re.match(ur'\[(.*)\]', stimuli)
    if match:
        return {'type': 'instruction',
                'instruction': match.groups()[0]}

    return {'type': 'prompt',
            'prompt': stimuli}


def load_stimuli(filename):
    with codecs.open(filename, 'r', 'utf-8') as f:
        data = f.read()
        data = data.replace('\n', '')

    return parse_stimuli(data)


def parse_torgo(path):
    # Search and parse recordings in the TORGO db
    unmatches = []
    utterances = {}

    for root, dirnames, filenames in os.walk(path):
        matches = list(fnmatch.filter(filenames, '*.phn')) + list(fnmatch.filter(filenames, '*.PHN'))
        for filename in matches:
            path = os.path.join(root, filename)

            utterance = {}

            match = re.search(torgo_phn_pattern, path, re.IGNORECASE)

            if match is None:
                raise ValueError('File {} did not match the '
                                 'pattern of a TORGO recording ({})'.format(path,
                                                                            torgo_phn_pattern))

            utterance.update(match.groupdict())

            dirname = os.path.dirname(os.path.dirname(path))
            wav_filename = os.path.join(dirname,
                                        'wav_{}'.format(utterance['sensor']),
                                        '{:04d}.wav'.format(int(utterance['id'])))

            if os.path.isfile(wav_filename):
                utterance['audio_filename'] = wav_filename
                utterance.update(get_audio_info(wav_filename))

            else:
                utterance['audio_filename'] = None

            utterance['audio_transcription_filename'] = path
            utterance['audio_transcription'] = load_transcription(path,
                                                                  audio_length=utterance.get('audio_length', None))

            stimuli_filename = os.path.join(dirname,
                                            'prompts',
                                            '{:04d}.txt'.format(int(utterance['id'])))

            utterance['stimuli_filename'] = stimuli_filename
            stimuli = load_stimuli(stimuli_filename) if os.path.isfile(stimuli_filename) else None

            utterance['stimuli'] = stimuli

            utterance_id = '{speaker}_{session}_{id}'.format(**utterance)
            utterance['utterance_id'] = utterance_id
            utterance['recording_id'] = utterance_id

            utterance['start_time'] = None
            utterance['end_time'] = None

            if utterance_id in utterances:
                logging.warning('Duplicate utterance ID: {}.\n'
                                'Previous value:\n'
                                '{}\n'
                                'New value:\n'
                                '{}'.format(utterance_id,
                                            json.dumps(utterances[utterance_id], indent=4, sort_keys=True),
                                            json.dumps(utterance, indent=4, sort_keys=True))
                                )

            utterances[utterance_id] = utterance

    if len(unmatches):
        logging.warning('The following .phn files did not match the TORGO pattern:\n{}'.format('\n'.join(unmatches)))

    speakers = {speaker_id: {'gender': speaker_id[0].lower()}
                for speaker_id in {utt['speaker'] for utt in utterances.values()}}

    return {'utterances': utterances, 'speakers': speakers}


def main():
    args = docopt.docopt(__doc__)
    logging.basicConfig(level=logging.INFO)

    overwrite = args['--overwrite']
    output_json_path = args['<output_json_path>']

    if os.path.exists(output_json_path) and not overwrite:
        logging.warning('TORGO database (in JSON) {} already exists. Not overwriting.'.format(output_json_path))
        return

    if not os.path.isdir(os.path.dirname(output_json_path)):
        os.makedirs(os.path.dirname(output_json_path))

    logging.info('Parsing TORGO database')
    db = parse_torgo(args['<torgo_path>'])

    logging.info('Writing TORGO database (in JSON) to {}'.format(output_json_path))
    with codecs.open(output_json_path, 'w', 'utf-8') as f:
        json.dump(db, f, sort_keys=True, indent=4)


if __name__ == '__main__':
    main()