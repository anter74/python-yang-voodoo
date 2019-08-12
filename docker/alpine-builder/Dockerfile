FROM alpine:3.10.0

RUN apk add python3

RUN apk add git cmake swig python3-dev libxml2-dev libtool \
            py3-setuptools readline-dev libxslt-dev make \
            protobuf-c-dev libev-dev openssl-dev \
            boost-thread libffi-dev bison automake zlib-dev \
            gcc g++ flex pcre-dev alpine-sdk vim musl-dev screen

RUN mkdir /opt/dev
WORKDIR /opt/dev

RUN \
      git clone https://github.com/CESNET/libyang.git

RUN \
      cd /opt/dev && \
      git clone https://github.com/allena29/libyang-cffi.git && \
      git clone https://github.com/allena29/python-yang-voodoo.git /working && \
      cd /working && \
      pip3 install -r requirements.txt

# libyang
RUN \
      cd /opt/dev && \
      cd libyang && \
      git checkout v1.0-r3 && \
      mkdir build && cd build && \
      cmake .. && \
      make -j6  && \
      make install && \
      ln -s /usr/local/lib64/*yang* /usr/local/lib

RUN \
      cd /working && \
      git checkout devel && \
      LIBYANG_INSTALL=system python3 setup.py install
RUN \
      cd /opt/dev && \
      cd libyang-cffi && \
      git checkout libyang-data-tree && \
      echo "#!/bin/bash" >rebuild.sh && \
      LIBYANG_INSTALL=system python3 setup.py install

RUN \
      cd /working && \
      git checkout devel && \
      LIBYANG_INSTALL=system python3 setup.py install
