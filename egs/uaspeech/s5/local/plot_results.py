#!/usr/bin/env python

import glob
import json
import pandas as pd
import re
import pylab

__author__ = 'rmarxer'


SIDD_BEST_RESULTS = [86.87, 69.54, 62.98, 28.71]


def analyze(df):
    df['accuracy'] = (df['total'] - df['errors']) * 100.0 / df['total']

    df['intelligibility_class'] = df['intelligibility_class'].astype('category',
                                                                     categories=['high', 'mid', 'low', 'very low'],
                                                                     ordered=True)

    df['setting'] = df['setting'].astype('category',
                                         categories=['leave_one_out', 'adapt_to_one', 'sidd'],
                                         ordered=True)

    grouped = df.groupby(['setting', 'model', 'test', 'intelligibility_class'])

    described = grouped.accuracy.describe()

    x = described.loc[:, 'tri3b_adapt', 'uaspeechvocab', :, 'mean'].unstack('setting')

    # Taken from the paper: http://www.slpat.org/slpat2015/papers/sehgal-cunningham.pdf
    x['sidd'] = SIDD_BEST_RESULTS

    x.plot(kind='bar')
    pylab.show()


def collect():
    uaspeech_filename = 'results/tmp/uaspeech.json'
    with open(uaspeech_filename) as f:
        speakers = json.load(f)['speakers']

    result_filenames = glob.glob("results/*/*/exp/*/decode_*/wer_*")
    results = []

    for filename in result_filenames:
        with open(filename, 'r') as f:
            lines = f.readlines()

        line = lines[1].strip()

        match = re.match(r"%WER (?P<wer>\d+(?:.\d*)?) "
                         r"\[ (?P<errors>\d+) "
                         r"/ (?P<total>\d+), "
                         r"(?P<insertions>\d+) ins, "
                         r"(?P<deletions>\d+) del, "
                         r"(?P<substitutions>\d+) sub \]", line)

        if match is None:
            raise ValueError('Line "{}" does not match the pattern.')

        result = match.groupdict()
        result['errors'] = int(result['errors'])
        result['total'] = int(result['total'])
        result['insertions'] = int(result['insertions'])
        result['deletions'] = int(result['deletions'])
        result['substitutions'] = int(result['substitutions'])
        result['wer'] = float(result['wer'])

        tokens = filename.split('/')

        result['setting'] = tokens[1]
        result['setting_param'] = tokens[2]
        result['model'] = tokens[4]
        result['test'] = tokens[5].replace('decode_', '').replace('_test', '')
        result['language_model_weight'] = int(tokens[6].replace('wer_', ''))

        result.update(speakers[result['setting_param']])

        results.append(result)

    df = pd.DataFrame(results)
    df.to_json('results.json')
    return df


def main():
    try:
        df = pd.read_json('results.json')

    except (ValueError, KeyError) as _:
        df = collect()

    analyze(df)

    return df


if __name__ == '__main__':
    main()
