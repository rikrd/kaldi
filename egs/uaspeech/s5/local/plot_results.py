import glob
import pandas as pd
import re

__author__ = 'rmarxer'


def main():
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

        tokens = filename.split('/')

        result['setting'] = tokens[1]
        result['setting_param'] = tokens[2]
        result['model'] = tokens[4]
        result['test'] = tokens[5].replace('decode_', '').replace('_test', '')
        result['language_model_weight'] = tokens[6].replace('wer_', '')

        results.append(result)

    df = pd.DataFrame(results)
    
    print(df)

    return

if __name__ == '__main__':
    main()
