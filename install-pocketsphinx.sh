#!/bin/sh

set -v -e -x

ncpu=-j`grep -c ^processor /proc/cpuinfo`

WORK=`mktemp -d`
cd $WORK
curl -L "http://downloads.sourceforge.net/project/cmusphinx/sphinxbase/5prealpha/sphinxbase-5prealpha.tar.gz?r=http%3A%2F%2Fsourceforge.net%2Fprojects%2Fcmusphinx%2Ffiles%2Fsphinxbase%2F5prealpha%2F&ts=1444324739&use_mirror=skylineservers" | tar xzf -
cd sphinxbase-*
./configure
make $ncpu
make install

cd $WORK
curl -L https://github.com/luser/pocketsphinx/archive/gst-extra-timestamps.tar.gz | tar xzf -
cd pocketsphinx-gst-extra-timestamps
./autogen.sh
make $ncpu
make install

cd /tmp
rm -rf $WORK
