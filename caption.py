#!/usr/bin/env python
#
# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from __future__ import print_function

import argparse
import codecs
import gi
gi.require_version('Gst', '1.0')
from gi.repository import GObject, Gst
from pycaption import SRTWriter, WebVTTWriter, CaptionSet, Caption, CaptionNode

GObject.threads_init()
Gst.init(None)

def caption(url=None, hmm=None, lm=None, dict=None,
            caption_format='webvtt'):
    if url is None:
        raise Exception('No URL specified!')
    pipeline = Gst.parse_launch('uridecodebin name=source ! audioconvert !' +
                                ' audioresample ! pocketsphinx name=asr !' +
                                ' fakesink')
    source = pipeline.get_by_name('source')
    source.set_property('uri', url)
    pocketsphinx = pipeline.get_by_name('asr')
    if hmm:
        pocketsphinx.set_property('hmm', hmm)
    if lm:
        pocketsphinx.set_property('lm', lm)
    if dict:
        pocketsphinx.set_property('dict', dict)

    bus = pipeline.get_bus()

    # Start playing
    pipeline.set_state(Gst.State.PLAYING)

    writer = WebVTTWriter()
    yield writer.HEADER

    # Wait until error or EOS
    while True:
        try:
            msg = bus.timed_pop(Gst.CLOCK_TIME_NONE)
            if msg:
                #if msg.get_structure():
                #    print(msg.get_structure().to_string())

                if msg.type == Gst.MessageType.EOS:
                    break
                struct = msg.get_structure()
                if struct and struct.get_name() == 'pocketsphinx':
                    if struct['final']:
                        c = Caption()
                        c.start = struct['start_time'] / Gst.USECOND
                        c.end = struct['end_time'] / Gst.USECOND
                        c.nodes.append(CaptionNode.create_text(struct['hypothesis']))
                        yield writer._write_caption(c)
        except KeyboardInterrupt:
            pipeline.send_event(Gst.Event.new_eos())

    # Free resources
    pipeline.set_state(Gst.State.NULL)


def print_captions(**kwargs):
    for c in caption(**kwargs):
        print(c)


def get_parser():
    parser = argparse.ArgumentParser(description='Recognize speech from audio')
    parser.add_argument('url', help='URL to a media file')
    parser.add_argument('--hmm',
                        help='Path to a pocketsphinx HMM data directory')
    parser.add_argument('--lm',
                        help='Path to a pocketsphinx language model file')
    parser.add_argument('--dict',
                        help='Path to a pocketsphinx CMU dictionary file')
    return parser

if __name__ == '__main__':
    parser = get_parser()
    args = parser.parse_args()
    print_captions(**vars(args))
