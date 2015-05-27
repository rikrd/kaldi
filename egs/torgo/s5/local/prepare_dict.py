#!/usr/bin/env python

"""prepare_cmudict.py

Prepares the CMUdict dictionary files necessary for Kaldi training using as input the JSON file.

The files it creates are [starred are optional]:
lexicon.txt
nonsilence_phones.txt
silence_phones.txt
optional_silence.txt
extra_questions.txt
reco2file_and_channel*
utt2spk
spk2gender*


Usage:
prepare_cmudict.py <output_dir>
prepare_cmudict.py --help

Options:
<output_dir>                output directory
--help, -h                  display this help screen
"""

from __future__ import print_function, unicode_literals
import codecs
import logging
import os
import locale
import subprocess
import urllib

import docopt

__author__ = 'rmarxer'


def c_sort(x):
    locale.setlocale(locale.LC_ALL, ('C', ''))
    x.sort(cmp=locale.strcoll)
    return x


def validate_kaldi_dict(dict_dir, options=''):
    cmd = 'utils/validate_dict_dir.pl {options} {dict_dir}'.format(dict_dir=dict_dir,
                                                                   options=options)
    logging.info(cmd)
    subprocess.call(cmd, shell=True)


def write_sorted(directory, filename, format_pattern, utterance_set):
    lines = [format_pattern.format(**utt)
             for utt in utterance_set]
    lines = c_sort(lines)

    with open(os.path.join(directory, filename), 'w') as f:
        f.writelines(['{}\n'.format(line) for line in lines])


def prepare_kaldi_cmu_dict(output_dir,
                           optional_silence_phone='sil',
                           extra_words={},
                           extra_silence_phones=set()):
    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)

    # Download CMUDict if needed
    cmudict_url = 'http://svn.code.sf.net/p/cmusphinx/code/trunk/cmudict/cmudict-0.7b'
    cmudict_filename = os.path.join(output_dir, 'tmp', 'cmudict-0.7b')
    if not os.path.isfile(cmudict_filename):
        if not os.path.isdir(os.path.dirname(cmudict_filename)):
            os.makedirs(os.path.dirname(cmudict_filename))

        logging.warning('File {} not found.\nRetrieving it from: {} ...'.format(cmudict_filename, cmudict_url))
        urllib.urlretrieve(cmudict_url, cmudict_filename)

    # Parse CMUDict if needed
    lexicon = {}
    with codecs.open(cmudict_filename, 'r', 'latin-1') as f:
        for line in f:
            if line.startswith(';;;'):
                continue

            word, pronunciation = line.strip().split('  ', 2)
            lexicon[word.upper()] = pronunciation.lower()

    # Add extra words to the lexicon
    for word, pronunciation in extra_words.iteritems():
        lexicon[word.upper()] = pronunciation.lower()

    extra_silence_phones = extra_silence_phones

    # Write the optional silence (silence that gets added before word pronunciations in the Lexicon transducer)
    optionalsilence_filename = os.path.join(output_dir, 'optional_silence.txt')
    with codecs.open(optionalsilence_filename, 'w', encoding='utf-8') as f:
        lines = ['{}\n'.format(optional_silence_phone)]
        c_sort(lines)
        f.writelines(lines)

    extra_silence_phones.add(optional_silence_phone)

    # Write the silence phones
    silence_filename = os.path.join(output_dir, 'silence_phones.txt')
    with codecs.open(silence_filename, 'w', encoding='utf-8') as f:
        lines = ['{}\n'.format(phone) for phone in extra_silence_phones]
        c_sort(lines)
        f.writelines(lines)

    all_phones = set()
    for pronunciation in lexicon.values():
        all_phones |= set(pronunciation.split())

    nonsilence_phones = all_phones - extra_silence_phones

    # Write the nonsilence phones
    nonsilence_filename = os.path.join(output_dir, 'nonsilence_phones.txt')
    with codecs.open(nonsilence_filename, 'w', encoding='utf-8') as f:
        lines = ['{}\n'.format(phone) for phone in nonsilence_phones]
        c_sort(lines)
        f.writelines(lines)

    # Write the lexicon
    lexicon_filename = os.path.join(output_dir, 'lexicon.txt')
    with codecs.open(lexicon_filename, 'w', encoding='utf-8') as f:
        lines = ['{word} {pronunciation}\n'.format(word=key, pronunciation=value)
                 for key, value in lexicon.iteritems()]
        c_sort(lines)
        f.writelines(lines)

    return output_dir


def main():
    args = docopt.docopt(__doc__)

    output_dir = args['<output_dir>']

    # Create the data files needed by kaldi (lexicon.txt, silence_phones.txt, nonsilence_phones.txt, ...)
    prepare_kaldi_cmu_dict(output_dir,
                           optional_silence_phone='sil',
                           extra_words={'<SIL>': 'sil',
                                        '<UNK>': 'nsn'},
                           extra_silence_phones={'nsn'})

    # Validata the data files
    validate_kaldi_dict(output_dir)

    return

if __name__ == '__main__':
    main()
    