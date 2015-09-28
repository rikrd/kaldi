#!/usr/bin/env python

"""prepare_lm_anyword.py

Prepares the lang files necessary for Kaldi testing based on an existing lang directory.

The files it creates are [starred are optional]:
text
wav.scp
segments*
reco2file_and_channel*
utt2spk
spk2gender*


Usage:
prepare_lm_anyword.py [options] <lang_dir> <word_list_filename> <output_lang_dir>
prepare_lm_anyword.py --help

Options:
<lang_dir>                path to the existing lang directory
<word_list_filename>      file containing the possible words of the language
<output_lang_dir>         output directory root
--overwrite, -o           overwrite the output directory if it exists
--help, -h                display this help screen
"""

import math
import os
import shutil
import subprocess
import docopt
import logging

__author__ = 'rmarxer'


def validate_kaldi_lang(lang_dir, options=''):
    cmd = 'utils/validate_lang.pl {options} {lang_dir}'.format(lang_dir=lang_dir,
                                                               options=options)
    logging.info(cmd)
    subprocess.call(cmd, shell=True)


def read_symbols(syms_filename):
    table = {}
    with open(syms_filename, 'r') as f:
        for l in f:
            token, ind = l.strip().rsplit(' ', 1)
            table[token] = ind

    return table


def read_words(syms_filename):
    words = set()
    with open(syms_filename, 'r') as f:
        for l in f:
            tokens = l.strip().split(' ', 1)

            words.add(tokens[0])

    return words


def forced_choice_grammar(choices, word_syms_filename, epsilon='<eps>', backoff='#0', forbidden={'<s>', '</s>'}):
    # Unused parameters
    _, _ = epsilon, backoff

    word_symbols = read_symbols(word_syms_filename)

    # Select possible choices
    choices = {choice for choice in choices if choice in word_symbols and choice not in forbidden}

    # Probability for the choice transitions
    prob = math.log(len(choices))

    fst_text = ''

    for index, choice in enumerate(choices):
        state = 1

        fst_text += '0 1 {choice} {choice} {prob}\n'.format(choice=choice,
                                                            state=state,
                                                            prob=prob)

    fst_text += '1 {prob}\n'.format(prob=prob)

    return fst_text


def make_forced_choice_grammar(choices, word_syms_filename, out_filename):
    """
    w_syms = fst.read_symbols(words_file)
    g = fst.Acceptor(syms=w_syms)

    for choice in choices:
        g.add_arc(0, 1, choice)

    g.write(grammar_file)
    """
    fst_text = forced_choice_grammar(choices, word_syms_filename, epsilon='<eps>', backoff='#0')

    cmd = '$KALDI_ROOT/tools/openfst/bin/fstcompile ' \
          '--isymbols={word_syms} --osymbols={word_syms} ' \
          '--keep_isymbols=false --keep_osymbols=false ' \
          '- ' \
          '| fstarcsort --sort_type=ilabel > ' \
          '{out_filename}'.format(word_syms=word_syms_filename,
                                  out_filename=out_filename)
    p = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE)
    p.communicate(fst_text)


def main():
    args = docopt.docopt(__doc__)
    logging.basicConfig(level=logging.INFO)

    lang_dir = args['<lang_dir>']
    word_list_filename = args['<word_list_filename>']
    output_lang_dir = args['<output_lang_dir>']

    if not os.path.isdir(lang_dir):
        raise ValueError('{} does not exist'.format(lang_dir))

    if os.path.exists(output_lang_dir):
        if args['--overwrite']:
            shutil.rmtree(output_lang_dir)

        else:
            logging.warn('{} already exists. Exiting.'.format(output_lang_dir))
            return

    shutil.copytree(lang_dir, output_lang_dir)

    words = read_words(word_list_filename)
    make_forced_choice_grammar(words,
                               os.path.join(output_lang_dir, 'words.txt'),
                               os.path.join(output_lang_dir, 'G.fst'))

    # Validata the lang files
    validate_kaldi_lang(output_lang_dir)


if __name__ == '__main__':
    main()
