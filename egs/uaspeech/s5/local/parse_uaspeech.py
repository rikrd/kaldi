#!/usr/bin/env python
"""parse_uaspeech.py

Parses the UASPEECH database into a JSON file

Usage:
parse_uaspeech.py [options] <uaspeech_path> <output_json_path>
parse_uaspeech.py --help

Options:
<uaspeech_path>             path to the UASPEECH dataset
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
import htk

import docopt

__author__ = 'rmarxer'

# Pattern to match paths such as:
# /path/to/UASPEECH/audio/F02/F02_B1_LE_M2.wav
uaspeech_wav_pattern = r'.*/audio(/control)?/(?P<speaker>.*)' \
                       r'/(?P<utterance_id>(?P=speaker)_B(?P<block>.*)_(?P<word_id>.*)_M(?P<microphone>.*))\.wav'


def clean_prompt(prompt):
    return prompt.upper() \
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


def load_prompts(uaspeech_path, utterances):
    speaker_wordlist_filename = os.path.join(uaspeech_path, 'speaker_wordlist.xls')

    import xlrd
    xls = xlrd.open_workbook(speaker_wordlist_filename)

    # Parse the wordlist sheet
    words = {row[1].value: clean_prompt(row[0].value) for row in list(xls.sheet_by_index(1).get_rows())[1:]}

    # Gather the prompts
    prompts = {}
    for utterance_id, utterance in utterances.iteritems():
        word_id = utterance['word_id']
        key = '{}{}'.format('B{}_'.format(utterance['block']) if word_id.startswith('UW') else '',
                            word_id)
        prompts[utterance_id] = words[key]

    return prompts


def _get_col_value(rows, row_index, col_index):
    value = rows[row_index][col_index].value

    if rows[row_index+1][col_index].value:
        value += ' {}'.format(rows[row_index+1][col_index].value)

    return value


def _parse_intelligibility(intell_string):
    return re.match(r"(?P<intelligibility_class>.*) "
                    r"\((?P<intelligibility_percentage>\d+(?:.\d+)?)%\)$", intell_string).groupdict()


def load_speakers(uaspeech_path, speakers):
    speaker_wordlist_filename = os.path.join(uaspeech_path, 'speaker_wordlist.xls')

    import xlrd
    xls = xlrd.open_workbook(speaker_wordlist_filename)

    # Parse the speaker sheet
    rows = list(xls.sheet_by_index(0).get_rows())
    for i, row in enumerate(rows):
        speaker = row[0].value.strip()
        if speaker in speakers:
            speakers[speaker].update({
                'age': _get_col_value(rows, i, 1),
                'dysarthria_diagnosis': _get_col_value(rows, i, 3),
                'motor_control': _get_col_value(rows, i, 4)
            })

            speakers[speaker].update(_parse_intelligibility(_get_col_value(rows, i, 2)))

            s = speakers[speaker]

            s['intelligibility_class'] = s['intelligibility_class'].lower()
            s['intelligibility_percentage'] = float(s['intelligibility_percentage'])

    return speakers


def load_transcription(uaspeech_path, speaker):
    mlf_filename = os.path.join(uaspeech_path, 'mlf', speaker, '{}_word.mlf'.format(speaker))

    if not os.path.isfile(mlf_filename):
        logging.warning('Could not find the MLF file {}'.format(mlf_filename))
        return {}

    mlf = htk.load_mlf(mlf_filename)

    transcriptions = {key[2:-4]: value[0][0].symbol for key, value in mlf.iteritems()}

    return transcriptions


def parse_uaspeech(uaspeech_path):
    # Search and parse recordings in the UASPEECH db
    utterances = {}

    wav_filenames = []
    for root, dirnames, filenames in os.walk(uaspeech_path):
        wav_filenames += [os.path.join(root, filename) for filename in fnmatch.filter(filenames, '*.wav')]

    for i, filename in enumerate(wav_filenames):
        logging.info('Processing WAV file {: 5d}/{: 5d} [ {} ] ...'.format(i+1, len(wav_filenames), filename))

        path = os.path.join(root, filename)

        utterance = {}

        match = re.search(uaspeech_wav_pattern, path, re.IGNORECASE)

        if match is None:
            logging.warning('File {} did not match the '
                            'pattern of a UASPEECH recording ({}). Skipping...'.format(path,
                                                                                       uaspeech_wav_pattern))
            continue

        utterance.update(match.groupdict())

        utterance_id = utterance['utterance_id']
        utterance['recording_id'] = utterance_id

        wav_filename = path

        if os.path.isfile(wav_filename):
            utterance['audio_filename'] = wav_filename

            # Some files in UASPEECH (M01 and F04 specially) have corrupted headers
            utterance['audio_rspecifier'] = 'local/wav_passthrough.py {} - |'.format(wav_filename)

            # utterance.update(get_audio_info(wav_filename))

        else:
            utterance['audio_filename'] = None
            utterance['audio_rspecifier'] = None

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

    speakers = {speaker_id: {'gender': speaker_id[-3].lower(),
                             'type': 'control' if speaker_id.startswith('C') else 'dysarthric'}
                for speaker_id
                in {utt['speaker'] for utt in utterances.values()}}

    # Load the transcriptions (MLF files)
    transcriptions = {}
    for speaker in speakers:
        mlf_transcriptions = load_transcription(uaspeech_path, speaker)
        transcriptions.update(mlf_transcriptions)

    # Load the prompts (from the speaker_wordlist.xls file)
    prompts = load_prompts(uaspeech_path, utterances)

    # Load the speaker properties (from the speaker_wordlist.xls file)
    speakers = load_speakers(uaspeech_path, speakers)

    for utterance_id in utterances:
        prompt = prompts[utterance_id]
        transcription = transcriptions.get(utterance_id, prompt)

        utterances[utterance_id]['audio_transcription'] = transcription
        utterances[utterance_id]['audio_prompt'] = prompt

        if not transcription == prompt:
            logging.warning('The transcription does not match the prompt\n'
                            '{} != {}'.format(transcription, prompt))

    return {'utterances': utterances, 'speakers': speakers}


def main():
    args = docopt.docopt(__doc__)
    logging.basicConfig(level=logging.INFO)

    overwrite = args['--overwrite']
    output_json_path = args['<output_json_path>']

    if os.path.exists(output_json_path) and not overwrite:
        logging.warning('UASPEECH database (in JSON) {} already exists. Not overwriting.'.format(output_json_path))
        return

    if not os.path.isdir(os.path.dirname(os.path.abspath(output_json_path))):
        os.makedirs(os.path.dirname(output_json_path))

    logging.info('Parsing UASPEECH database')
    db = parse_uaspeech(args['<uaspeech_path>'])

    logging.info('Writing UASPEECH database (in JSON) to {}'.format(output_json_path))
    with codecs.open(output_json_path, 'w', 'utf-8') as f:
        json.dump(db, f, sort_keys=True, indent=4)


if __name__ == '__main__':
    main()