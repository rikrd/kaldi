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
import re
import itertools

__author__ = 'rmarxer'


def get_and_parse_cmudict(work_dir):
    cmudict_dir = os.path.join(work_dir, 'tmp')

    # Download CMUDict
    cmudict_url = 'http://svn.code.sf.net/p/cmusphinx/code/trunk/cmudict'
    cmudict_files = ['cmudict-0.7b', 'cmudict-0.7b.phones', 'cmudict-0.7b.symbols']
    for filename in cmudict_files:
        download(os.path.join(cmudict_url, filename), os.path.join(cmudict_dir, filename))

    # Parse CMUDict lexicon
    lexicon = {}
    with codecs.open(os.path.join(cmudict_dir, 'cmudict-0.7b'), 'r', 'latin-1') as f:
        for line in f:
            if line.startswith(';;;'):
                continue

            word, pronunciation = line.strip().split('  ', 2)
            lexicon[word.upper()] = pronunciation.lower()

    # Prepare the extra questions for CMUDict (different stress of each phone)
    extra_questions = []
    nonsilence_phones = []
    with codecs.open(os.path.join(cmudict_dir, 'cmudict-0.7b.symbols'), 'r', 'latin-1') as fsymb:
        with codecs.open(os.path.join(cmudict_dir, 'cmudict-0.7b.phones'), 'r', 'latin-1') as fphones:
            symbols_txt = fsymb.read()

            # Currently we don't use the phone types, it could be used to create other extra questions
            _ = [tuple(l.strip().split()) for l in fphones.readlines() if l.strip()]

            # Results contains a list of matches.  Matches are tuples containing
            # the full phone symbol, the phone and the stress mark.
            #   e.g. ('AA', 'AA', ''), ('AA0', 'AA', '0')
            results = re.findall(r'^((\D+?)(\d)?)$', symbols_txt, re.MULTILINE)

            # Group the phone symbols by stress marker and create the questions
            groups = itertools.groupby(sorted(results, key=lambda x: x[2]), key=lambda x: x[2])
            for stress, phonesymbols_stress in groups:
                phonesymbols = zip(*list(phonesymbols_stress))[0]
                extra_questions.append(phonesymbols)

            # Group the phone symbols by phone and create the nonsilence_phones
            groups = itertools.groupby(sorted(results, key=lambda x: x[1]), key=lambda x: x[1])
            for phone, phonesymbols_stress in groups:
                phonesymbols = zip(*list(phonesymbols_stress))[0]
                nonsilence_phones.append(phonesymbols)

    silence_phones = []

    return {'lexicon': lexicon,
            'extra_questions': extra_questions,
            'nonsilence_phones': nonsilence_phones,
            'silence_phones': silence_phones}


def download(url, filename):
    if not os.path.isfile(filename):
        if not os.path.isdir(os.path.dirname(filename)):
            os.makedirs(os.path.dirname(filename))

        logging.warning('File {} not found.\nRetrieving it from: {} ...'.format(filename, url))
        urllib.urlretrieve(url, filename)


def validate_kaldi_dict(dict_dir, options=''):
    cmd = 'utils/validate_dict_dir.pl {options} {dict_dir}'.format(dict_dir=dict_dir,
                                                                   options=options)
    logging.info(cmd)
    subprocess.call(cmd, shell=True)


def c_sort(x):
    locale.setlocale(locale.LC_ALL, ('C', ''))
    return sorted(x, cmp=locale.strcoll)


def write_lines_sorted(f, lines):
    lines = c_sort(list(lines))
    f.writelines(['{}\n'.format(line) for line in lines])


def write_pattern_sorted(directory, filename, format_pattern, utterance_set):
    with open(os.path.join(directory, filename), 'w') as f:
        lines = [format_pattern.format(**utt)
                 for utt in utterance_set]
        write_lines_sorted(f, lines)


def prepare_kaldi_dict(output_dir,
                       lexicon_info,
                       optional_silence_phone='sil',
                       extra_words={},
                       extra_silence_phones=set(),
                       add_silence_question=True):
    """Prepares the dict folder that Kaldi expects.

    :param output_dir:
    :param lexicon_info: It is a dictionary containing:
        'lexicon' (dictionary of word to pronunciation)
        'extra_questions' (list of clusters of phones grouped by question)
        'nonsilence_phones' (list of non-silence phones grouped by phone root)
        'silence_phones' (list of silence phone symbols)
    :param optional_silence_phone: The phone used to pad the begining of words in the L.fst (short pause)
    :param extra_words: A dictionary with the extra words/pronunciations to add to the lexicon
    :param extra_silence_phones: The extra silence phones (no need to include the optional_silence_phone)
    :return:
    """
    lexicon = lexicon_info['lexicon']
    extra_questions = lexicon_info['extra_questions']
    nonsilence_phones = lexicon_info['nonsilence_phones']
    silence_phones = set(lexicon_info['silence_phones'])

    # Add extra words to the lexicon
    for word, pronunciation in extra_words.iteritems():
        lexicon[word.upper()] = pronunciation.lower()

    silence_phones |= extra_silence_phones

    # Write the optional silence (silence that gets added before word pronunciations in the Lexicon transducer)
    optionalsilence_filename = os.path.join(output_dir, 'optional_silence.txt')
    with codecs.open(optionalsilence_filename, 'w', encoding='utf-8') as f:
        write_lines_sorted(f, [optional_silence_phone])

    silence_phones.add(optional_silence_phone)

    # Write the silence phones
    silence_filename = os.path.join(output_dir, 'silence_phones.txt')
    with codecs.open(silence_filename, 'w', encoding='utf-8') as f:
        write_lines_sorted(f, silence_phones)

    all_phones = set()
    for pronunciation in lexicon.values():
        all_phones |= set(pronunciation.split())

    extra_nonsilence_phones = all_phones - (set(itertools.chain(nonsilence_phones)) | silence_phones)
    if extra_nonsilence_phones:
        raise ValueError('Detected the following extra phones in the lexicon '
                         'that do not appear in nonsilence nor '
                         'silence phone sets: {}'.format(' '.join(extra_nonsilence_phones)))

    # Write the nonsilence phones
    nonsilence_filename = os.path.join(output_dir, 'nonsilence_phones.txt')
    with codecs.open(nonsilence_filename, 'w', encoding='utf-8') as f:
        lines = [' '.join(c_sort(nonsilence_phone)) for nonsilence_phone in nonsilence_phones]
        write_lines_sorted(f, lines)

    # Write the extra questions
    other_questions = []
    if add_silence_question:
        other_questions.append(silence_phones)

    extra_questions_filename = os.path.join(output_dir, 'extra_questions.txt')
    with codecs.open(extra_questions_filename, 'w', encoding='utf-8') as f:
        lines = [' '.join(c_sort(extra_question)) for extra_question in other_questions + extra_questions]
        write_lines_sorted(f, lines)

    # Write the lexicon
    lexicon_filename = os.path.join(output_dir, 'lexicon.txt')
    with codecs.open(lexicon_filename, 'w', encoding='utf-8') as f:
        lines = ['{word} {pronunciation}'.format(word=key, pronunciation=value)
                 for key, value in lexicon.iteritems()]
        write_lines_sorted(f, lines)

    return output_dir


def main():
    args = docopt.docopt(__doc__)

    output_dir = args['<output_dir>']

    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)

    # Download if necessary and parse the CMU dictionary
    lexicon_info = get_and_parse_cmudict(output_dir)

    # Create the data files needed by kaldi (lexicon.txt, silence_phones.txt, nonsilence_phones.txt, ...)
    prepare_kaldi_dict(output_dir,
                       lexicon_info,
                       optional_silence_phone='SIL',
                       extra_words={'<SIL>': 'SIL',
                                    '<UNK>': 'NOI'},
                       extra_silence_phones={'NOI'})

    # Validata the data files
    validate_kaldi_dict(output_dir)

    return

if __name__ == '__main__':
    main()
