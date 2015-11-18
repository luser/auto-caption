#!/bin/sh

set -e

test -z $1 && exit 1;

python `dirname $0`/caption.py \
 --hmm=/opt/pocketsphinx/model/en-us/en-us \
 --lm=/opt/pocketsphinx/model/en-us/en-us.lm.bin \
 $*
