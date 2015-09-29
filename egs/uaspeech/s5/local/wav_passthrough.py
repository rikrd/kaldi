#!/usr/bin/env python
"""wav_passthrough.py

Reads (parses) and rewrites the WAV file to try to solve any corruptions
that may cause Kaldi to not read it correctly

Usage:
wav_passthrough.py <input_wav> <output_wav>
wav_passthrough.py --help

Options:
<input_wav>             path to the input wav file (use - for stdin)
<output_wav>            path to the output wav file (use - for stdout)
--help, -h              display this help screen
"""

from __future__ import print_function, unicode_literals
import wave
import docopt
import sys
import io

def main():
    args = docopt.docopt(__doc__)

    try:
        if args['<input_wav>'] == '-':
            f = sys.stdin
        else:
            f = open(args['<input_wav>'], 'rb')

        if args['<output_wav>'] == '-':
            fo = sys.stdout
        else:
            fo = open(args['<output_wav>'], 'wb')

        output = io.BytesIO()

        w = wave.open(f, 'r')
        wo = wave.open(output, 'wb')

        wo.setparams(w.getparams())
        nframes = w.getnframes()
        wo.setnframes(nframes)
        wo.writeframes(w.readframes(nframes))

        fo.write(output.getvalue())

    finally:
        w.close()
        wo.close()

        output.close()

        f.close()
        fo.close()


if __name__ == '__main__':
    main()