#!/bin/sh

set -v -e -x

mkdir -p /opt/pocketsphinx/model/en-us/en-us

cd /tmp
curl -f -L -o cmusphinx-en-us-5.2.tar.gz http://skylineservers.dl.sourceforge.net/project/cmusphinx/Acoustic%20and%20Language%20Models/US%20English%20Generic%20Acoustic%20Model/cmusphinx-en-us-5.2.tar.gz
curl -f -L -o cmusphinx-5.0-en-us.lm.gz http://skylineservers.dl.sourceforge.net/project/cmusphinx/Acoustic%20and%20Language%20Models/US%20English%20Generic%20Language%20Model/cmusphinx-5.0-en-us.lm.gz
curl -f -L -o cmusphinx-en-us-8khz-5.1.tar.gz http://iweb.dl.sourceforge.net/project/cmusphinx/Acoustic%20and%20Language%20Models/US%20English%20Generic%20Acoustic%20Model/cmusphinx-en-us-8khz-5.1.tar.gz

gzip -dc /tmp/cmusphinx-5.0-en-us.lm.gz > /opt/pocketsphinx/model/en-us/en-us.lm.bin
cd /opt/pocketsphinx/model/en-us/ && tar xzf /tmp/cmusphinx-en-us-8khz-5.1.tar.gz
cd /opt/pocketsphinx/model/en-us/en-us && tar xzf /tmp/cmusphinx-en-us-5.2.tar.gz --strip-components=1

rm /tmp/cmusphinx-5.0-en-us.lm.gz /tmp/cmusphinx-en-us-5.2.tar.gz /tmp/cmusphinx-en-us-8khz-5.1.tar.gz

