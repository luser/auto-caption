FROM ubuntu:15.04
# If host is running squid-deb-proxy on port 8000, populate /etc/apt/apt.conf.d/30proxy
# By default, squid-deb-proxy 403s unknown sources, so apt shouldn't proxy ppa.launchpad.net
RUN awk '/^[a-z]+[0-9]+\t00000000/ { printf("%d.%d.%d.%d\n", "0x" substr($3, 7, 2), "0x" substr($3, 5, 2), "0x" substr($3, 3, 2), "0x" substr($3, 1, 2)) }' < /proc/net/route > /tmp/host_ip.txt
RUN perl -pe 'use IO::Socket::INET; chomp; $socket = new IO::Socket::INET(PeerHost=>$_,PeerPort=>"8000"); print $socket "HEAD /\n\n"; my $data; $socket->recv($data,1024); exit($data !~ /squid-deb-proxy/)' <  /tmp/host_ip.txt \
  && (echo "Acquire::http::Proxy \"http://$(cat /tmp/host_ip.txt):8000\";" > /etc/apt/apt.conf.d/30proxy) \
  && (echo "Acquire::http::Proxy::ppa.launchpad.net DIRECT;" >> /etc/apt/apt.conf.d/30proxy) \
  || echo "No squid-deb-proxy detected on docker host"
RUN apt-get update && apt-get install -y curl
# Download latest pocketsphinx English language model/HMM
ADD download-pocketsphinx-lm.sh /tmp/
RUN sh /tmp/download-pocketsphinx-lm.sh
RUN apt-get install -y pkg-config build-essential bison swig2.0 python-dev python-pip psmisc gstreamer1.0 gstreamer1.0-dev gstreamer1.0-tools python-gst-1.0 libxml2-dev libxslt-dev autoconf automake libtool
RUN pip install pycaption
ADD install-pocketsphinx.sh /tmp/
RUN sh /tmp/install-pocketsphinx.sh
RUN useradd -d /home/user -s /bin/bash -m user
ADD caption.py run.sh /home/user/
RUN chmod +x /home/user/caption.py /home/user/run.sh
USER user
ENV LD_LIBRARY_PATH=/usr/local/lib
ENV GST_PLUGIN_PATH=/usr/local/lib/gstreamer-1.0
WORKDIR /home/user
