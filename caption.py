#!/usr/bin/env python
from __future__ import print_function

import argparse
import codecs
import gi
gi.require_version('Gst', '1.0')
from gi.repository import GObject, Gst
from pycaption import SRTWriter, WebVTTWriter, CaptionSet, Caption, CaptionNode

GObject.threads_init()
Gst.init(None)

def run_pipeline(url=None, hmm=None, lm=None, dict=None,
                 caption_format='webvtt', out_file=None):
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

    cap_set = CaptionSet()
    captions = []

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
                        c.start = struct['start_time'] / Gst.USECOND;
                        c.end = struct['end_time'] / Gst.USECOND;
                        c.nodes.append(CaptionNode.create_text(struct['hypothesis']))
                        captions.append(c)
        except KeyboardInterrupt:
            pipeline.send_event(Gst.Event.new_eos())

    # Free resources
    pipeline.set_state(Gst.State.NULL)

    cap_set.set_captions('en-US', captions)
    writer = SRTWriter() if caption_format == 'srt' else WebVTTWriter()
    caption_data = writer.write(cap_set)
    if out_file is not None:
        codecs.open(out_file, 'w', 'utf-8').write(caption_data)
    else:
        print(caption_data)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Recognize speech from audio')
    parser.add_argument('url', help='URL to a media file')
    parser.add_argument('--hmm',
                        help='Path to a pocketsphinx HMM data directory')
    parser.add_argument('--lm',
                        help='Path to a pocketsphinx language model file')
    parser.add_argument('--dict',
                        help='Path to a pocketsphinx CMU dictionary file')
    parser.add_argument('--caption-format', choices=['srt', 'webvtt'],
                        default='webvtt',
                        help='Format of output captions')
    parser.add_argument('--out-file', metavar='FILE',
                        help='Write captions to FILE (default is stdout)')
    args = parser.parse_args()
    run_pipeline(**vars(args))
