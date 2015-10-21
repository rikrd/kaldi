#!/usr/bin/env python

"""show_alignment.py

Shows the alignment result from a alignment ark file produced by Kaldi.

Uses the following command to get the alignment:
ali-to-phones --ctm-output my.mdl ark,t:"gunzip -c ali.1.gz|" - | utils/int2sym.pl -f 5 phones.txt -

Usage:
show_alignment.py [options] <alignment_file> <lang_directory> [<utterance_id>]
show_alignment.py --help

Options:
<alignment_file>          path to alignment file
<lang_directory>          path to alignment file
<utternace_id>            file containing the possible words of the language
--help, -h                display this help screen
"""


from __future__ import print_function, unicode_literals
import os
import json
import random
import subprocess
import scipy
import scipy.io.wavfile as wavefile
import matplotlib.pyplot as pplot
import docopt
import bottle

__author__ = 'rmarxer'


def load_alignments(alignment_filename, lang_directory):
    print('Loading {} ...'.format(alignment_filename))

    model_filename = os.path.join(os.path.dirname(alignment_filename), 'final.mdl')

    lines = subprocess.check_output('ali-to-phones --print-args=false --ctm-output {} ark,t:"gunzip -c {}|" - '
                                    '| utils/int2sym.pl -f 5 {} -'.format(model_filename,
                                                                          alignment_filename,
                                                                          os.path.join(lang_directory,
                                                                                       'phones.txt')),
                                    stderr=None,
                                    shell=True)

    # CTM format e.g. F02_B1_C11_M2 1 0.00 4.53 SIL
    alignments = {}
    for l in lines.split('\n'):
        if not l.strip():
            continue

        utt_id, _, start, length, label = l.strip().split(' ')

        alignments.setdefault(utt_id, []).append((float(start), float(start)+float(length), label))

    return alignments


def show_alignment_matplotlib(utt_id, alignments):
    print('Showing {} ...'.format(utt_id))
    speaker, block, word, mic = utt_id.split('_')

    wav_filename = '/Users/rmarxer/data/UASPEECH/audio/{}{}/{}.wav'.format('control/' if speaker.startswith('C') else '',
                                                                           speaker,
                                                                           utt_id)

    print('Loading WAV {} ...'.format(wav_filename))
    rate, wav = wavefile.read(wav_filename)

    t = scipy.arange(len(wav)) / float(rate)

    pplot.plot(t, wav)
    segments = alignments[utt_id]
    print(segments)

    ax = pplot.gca()
    color_cycle = ax._get_lines.color_cycle

    colors = {}
    for start, end, label in segments:
        if label == 'SIL':
            continue

        normalized_label = label.replace('_B', '').replace('_E', '').replace('_I', '').replace('_S', '')
        if normalized_label not in colors:
            colors[normalized_label] = color_cycle.next()

        length = end-start
        pplot.axvspan(start, end, color=colors[normalized_label], alpha=0.5)

        ylim = ax.get_ylim()
        pplot.annotate(normalized_label,
                       horizontalalignment='center', verticalalignment='center', fontsize=12,
                       xy=(start + length/2.0, 1), xytext=(start + length/2.0, ylim[1]*0.9), textcoords='data')

    pplot.show()


def show_alignment_wavesurferjs(utt_id, alignments):
    print('Showing {} ...'.format(utt_id))
    speaker, block, word, mic = utt_id.split('_')

    wav_filename = '/Users/rmarxer/data/UASPEECH/audio/{}{}/{}.wav'.format('control/' if speaker.startswith('C') else '',
                                                                           speaker,
                                                                           utt_id)

    wav_filename = os.path.relpath(wav_filename, os.path.expanduser('~'))

    print('Loading WAV {} ...'.format(wav_filename))

    segments = alignments[utt_id]

    # Prepare the segments for the wavesurfer regions plugin
    segments_clean = [(start, end, label.replace('_B', '').replace('_E', '').replace('_I', '').replace('_S', ''))
                      for start, end, label in segments
                      if label != 'SIL']

    regions = []
    for start, end, label in segments_clean:
        rgba = 'rgba({},{},{}, 0.3)'.format(random.randint(0, 255),
                                            random.randint(0, 255),
                                            random.randint(0, 255))

        regions.append({'start': start,
                        'end': end,
                        'color': rgba,
                        'attributes': {
                            'label': label
                        }
                        })

    regions_add = ''
    for start, end, label in segments_clean:
        rgba = 'rgba({},{},{}, 0.3)'.format(random.randint(0, 255),
                                            random.randint(0, 255),
                                            random.randint(0, 255))

        regions_add += 'wavesurfer.addRegion({' \
                       'start: %f, ' \
                       'end: %f, ' \
                       'color: "%s",' \
                       'data: { label: "%s" },' \
                       '})\n' % (start, end, rgba, label)

    # Serve a web with one single element corresponding to the wavesurfer element
    index_html = '''
<html>
    <head>
        <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
        <title>Wave visualisation</title>

        <script src="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.5/js/bootstrap.min.js" integrity="sha256-Sk3nkD6mLTMOF0EOpNtsIry+s1CsaqQC1rVLTAy+0yc= sha512-K1qjQ+NcF2TYO/eI3M6v8EiNYZfA95pQumfvcVrTHtwQVDG+aHRqLi/ETn2uB+1JqwYqVG3LIvdm9lj6imS/pQ==" crossorigin="anonymous"></script>
        <link href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.5/css/bootstrap.min.css" rel="stylesheet" integrity="sha256-MfvZlkHCEqatNoGiOXveE8FIwMzZg4W85qfrfIFBfYc= sha512-dTfge/zgoMYpP7QbHy4gWMEGsbsdZeCXz7irItjcC3sPUFtf0kuFbDz/ixG7ArTxmDjLXDmezHubeNikyKGVyQ==" crossorigin="anonymous">

        <!-- wavesurfer.js -->
        <script src="js/wavesurfer.min.js"></script>

        <!-- regions plugin -->
        <script src="js/wavesurfer.regions.js"></script>

        <link rel="stylesheet" href="css/app.css" />
    </head>
    <body>
        <div id="wave">
        </div>
        <script>
            function loadRegions(regions) {
                regions.forEach(function (region) {
                    wavesurfer.addRegion(region);
                });
            }

            var wavesurfer = Object.create(WaveSurfer);

            wavesurfer.init({
                container: document.querySelector('#wave'),
                normalize: true,
                waveColor: 'violet',
                progressColor: 'purple'
            });

            wavesurfer.on('ready', function () {
                wavesurfer.util.ajax({
                    responseType: 'json',
                    url: '/regions'
                }).on('success', function (data) {
                    loadRegions(data);
                    wavesurfer.play();
                });
            });

            wavesurfer.load('%s');
        </script>
    </body>
</html>
    ''' % ('audio/' + wav_filename,)

    @bottle.route('/')
    def bottle_index():
        return index_html

    @bottle.route('/js/<filename:path>')
    def bottle_js(filename):
        return bottle.static_file(filename, root=os.path.join(os.path.dirname(__file__)))

    @bottle.route('/css/<filename:path>')
    def bottle_css(filename):
        return bottle.static_file(filename, root=os.path.join(os.path.dirname(__file__)))

    @bottle.route('/audio/<filename:path>')
    def bottle_audio(filename):
        return bottle.static_file(filename, root=os.path.expanduser('~'))

    @bottle.route('/regions')
    def bottle_regions():
        bottle.response.content_type = 'application/json'
        return json.dumps(regions)

    bottle.run(host='localhost', port=8080)

    # Open the web and enjoy


def main():
    args = docopt.docopt(__doc__)

    utt_id = None

    alignments = load_alignments(args['<alignment_file>'], args['<lang_directory>'])

    if not utt_id:
        utt_id = alignments.keys()[int(random.random()*len(alignments))]

    show_alignment_wavesurferjs(utt_id, alignments)


if __name__ == '__main__':
    main()
