#!/usr/bin/env python
#
# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from __future__ import print_function, unicode_literals

import argparse
import codecs
import gi
import os
import pycaption
import requests
import shutil
import subprocess
import sys
import tempfile
import urllib

from itertools import chain

def extract_audio(media_url, data, tempdir):
    path = os.path.join(tempdir, 'mediafile')
    urllib.urlretrieve(media_url, path)
    for filename, start, end in data:
        subprocess.check_call(['ffmpeg', '-loglevel', 'error',
                               '-i', path,
                               '-ss', str(start), '-to', str(end),
                               '-vn', '-acodec', 'pcm_s16le',
                               '-ar', '16000', '-ac', '1',
                               os.path.join(tempdir, filename)
                           ])


def get_captions(url):
    '''
    Given a url to a caption file, return a list of captions in the file.
    '''
    res = requests.get(url)
    if res.status_code != 200:
        print('Error fetching "%s": HTTP response %d' % (url, res.status_code))
        sys.exit(1)

    caps = res.text
    reader = pycaption.detect_format(caps)
    if not reader:
        print('Error: Could not determine caption format!')
        sys.exit(1)

    cap_set = reader().read(caps)
    langs = cap_set.get_languages()
    if len(langs) > 1:
        print('Error: too many languages in caption file: %s' % (', '.join(langs)))
        sys.exit(1)

    return cap_set.get_captions(langs[0])


def generate_sphinxtrain_data(captions, tempdir):
    '''
    Write a transcript.fileids file in tempdir containing a list of base
    filenames, one per caption in captions, and a transcript.transcription
    file in tempdir containing the caption text and filename for each
    caption.

    Yields tuples of (filename, start time, end time), where the times
    are in seconds from the start of the stream.
    '''
    with codecs.open(os.path.join(tempdir, 'transcript.fileids'), 'w', 'utf-8') as fileids, codecs.open(os.path.join(tempdir, 'transcript.transcription'), 'w', 'utf-8') as transcription:
        for i, c in enumerate(captions):
            filename = 'transcript_%04d' % i
            fileids.write(filename + '\n')
            transcription.write('<s> %s </s> (%s)\n' % (c.get_text(), filename))
            yield (filename + '.wav', c.start / 1000000.0, c.end / 1000000.0)


def fetch_and_extract(url, tempdir):
    path = os.path.join(tempdir, os.path.basename(url))
    urllib.urlretrieve(url, path)
    subprocess.check_call(['tar', 'xzf', path], cwd=tempdir)

def copy_existing_model(tempdir):
    shutil.copytree('/opt/pocketsphinx/model/en-us/en-us',
                    os.path.join(tempdir, 'en-us'))
    shutil.copy('/usr/local/share/pocketsphinx/model/en-us/cmudict-en-us.dict', tempdir)
    shutil.copy('/opt/pocketsphinx/model/en-us/en-us.lm.bin', tempdir)

def generate_acoustic_features(tempdir):
    subprocess.check_call(['sphinx_fe', '-argfile', 'en-us/feat.params',
                           '-samprate', '16000', '-c', 'transcript.fileids',
                           '-di', '.', '-do', '.', '-ei', 'wav', '-eo', 'mfc',
                           '-mswav', 'yes'], cwd=tempdir)

def accumulate_observation_counts(tempdir):
    extra = list(chain.from_iterable(
        l.strip().split() for l in open(os.path.join(tempdir, 'en-us',
                                                     'feat.params'), 'r')
        if any(l.startswith(x) for x in ('-feat ', '-agc ', '-cmn '))))
    subprocess.check_call(['/usr/local/libexec/sphinxtrain/bw',
                           '-hmmdir', 'en-us',
                           '-moddeffn', 'en-us/mdef',
                           '-ts2cbfn', '.cont.',
                           '-dictfn', 'cmudict-en-us.dict',
                           '-ctlfn', 'transcript.fileids',
                           '-lsnfn', 'transcript.transcription',
                           '-accumdir', '.',
                           '-lda', 'en-us/feature_transform'] + extra,
                          cwd=tempdir)


def create_mllr_transformation(tempdir):
    subprocess.check_call(['/usr/local/libexec/sphinxtrain/mllr_solve',
                           '-meanfn', 'en-us/means',
                           '-varfn', 'en-us/variances',
                           '-outmllrfn', 'mllr_matrix', '-accumdir', '.'],
                          cwd=tempdir)

def update_model_map(tempdir):
    shutil.copytree(os.path.join(tempdir, 'en-us'),
                    os.path.join(tempdir, 'en-us-adapt'))
    subprocess.check_call(['/usr/local/libexec/sphinxtrain/map_adapt',
                           '-moddeffn', 'en-us/mdef',
                           '-ts2cbfn', '.ptm.',
                           '-meanfn', 'en-us/means',
                           '-varfn', 'en-us/variances',
                           '-mixwfn', 'en-us/mixture_weights',
                           '-tmatfn', 'en-us/transition_matrices',
                           '-accumdir', '.',
                           '-mapmeanfn', 'en-us-adapt/means',
                           '-mapvarfn', 'en-us-adapt/variances',
                           '-mapmixwfn', 'en-us-adapt/mixture_weights',
                           '-maptmatfn', 'en-us-adapt/transition_matrices'],
                          cwd=tempdir)

def main():
    parser = argparse.ArgumentParser(description='Extract audio slices from a media file given a caption file')
    parser.add_argument('media_url', help='URL to a media file')
    parser.add_argument('caption_url', help='URL to a caption file')
    parser.add_argument('model_url', help='URL to a Pocketsphinx model',
                        nargs='?',
                        default=None)
    args = parser.parse_args()

    captions = get_captions(args.caption_url)
    try:
        tempdir = tempfile.mkdtemp('sphinxtrain')
        data = list(generate_sphinxtrain_data(captions, tempdir))
        extract_audio(args.media_url, data, tempdir)
        if args.model_url:
            fetch_and_extract(args.media_url, tempdir)
        else:
            copy_existing_model(tempdir)
        generate_acoustic_features(tempdir)
        accumulate_observation_counts(tempdir)
        update_model_map(tempdir)
        shutil.rmtree(os.path.join(tempdir, 'en-us'))
        shutil.move(os.path.join(tempdir, 'en-us-adapt'),
                    os.path.join(tempdir, 'en-us'))
        subprocess.check_call(['tar', 'czf',
                               os.path.join(os.getcwd(),
                                            'updated-model.tar.gz'),
                               'en-us'],
                              cwd=tempdir)
    finally:
        if os.path.isdir(tempdir):
            shutil.rmtree(tempdir)

if __name__ == '__main__':
    main()
