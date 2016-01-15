#!/usr/bin/python
#
# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from __future__ import print_function
from urlparse import urljoin

from etherpad_lite import EtherpadLiteClient

from caption import caption, get_parser as base_get_parser

def caption_to_etherpad(url, etherpad_url, api_key_file, **kwargs):
    api_url = urljoin(etherpad_url, '/api')
    pad_id = etherpad_url.split('/')[-1]

    apikey = open(api_key_file, 'rb').read()
    client = EtherpadLiteClient(base_url=api_url, api_version='1.2.13', base_params={'apikey': apikey})
    for c in caption(url, **kwargs):
        print(c)
        client.appendText(padID=pad_id, text=c + '\n')


def get_parser():
    parser = base_get_parser()
    parser.add_argument('etherpad_url',
                        help='URL of an Etherpad Lite pad in which to put transcription')
    parser.add_argument('api_key_file',
                        help='Path to a file containing Etherpad Lite API key')
    return parser


def main():
    parser = get_parser()
    args = parser.parse_args()
    kwargs = vars(args)
    caption_to_etherpad(**kwargs)


if __name__ == '__main__':
    main()
