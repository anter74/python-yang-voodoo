FROM alpine:3.10.0

RUN apk add python3

RUN apk add git cmake swig python3-dev libxml2-dev libtool \
            py3-setuptools readline-dev libxslt-dev make \
            protobuf-c-dev libev-dev openssl-dev \
            boost-thread libffi-dev bison automake zlib-dev \
            gcc g++ flex pcre-dev alpine-sdk vim musl-dev screen \
            librdkafka-dev

RUN mkdir /opt/dev && \
    adduser -D -g abuild builder && \
    passwd -d builder builder && \
    echo "builder    ALL=(ALL)  NOPASSWD: ALL" >>/etc/sudoers && \
    mkdir /pkgs && \
    chown builder /pkgs -R && \
    chown builder /var/cache -R && \
    chown builder /home/builder -R && \
    addgroup builder abuild

WORKDIR /opt/dev

RUN \
      wget https://files.pythonhosted.org/packages/c4/43/3f1e7d742e2a7925be180b6af5e0f67d38de2f37560365ac1a0b9a04c015/lxml-4.4.1.tar.gz && \
      tar xvfz lxml-4.4.1.tar.gz && \
      pip3 install wheel && \
      cd lxml-4.4.1 && \
      python3 setup.py bdist_wheel && \
      python3 -m pip install dist/*.whl && \
      mv dist/*.whl /pkgs

RUN \ 
      wget https://files.pythonhosted.org/packages/93/1a/ab8c62b5838722f29f3daffcc8d4bd61844aa9b5f437341cc890ceee483b/cffi-1.12.3.tar.gz && \
      tar xvfz cffi-1.12.3.tar.gz && \
      cd cffi-1.12.3 && \
      python3 setup.py bdist_wheel && \
      python3 -m pip install dist/*.whl && \
      mv dist/*.whl /pkgs 

RUN \
    sudo apk add librdkafka-dev && \
    wget https://files.pythonhosted.org/packages/c7/27/e7f6d54dafb050dcb66622742d8a39c5742ca6aa00c337b043738da78abf/confluent-kafka-1.1.0.tar.gz && \
    tar xvfz confluent-kafka-1.1.0.tar.gz && \
    cd confluent-kafka-1.1.0 && \
    python3 setup.py build bdist_wheel && \
    cp dist/*.whl /pkgs && \
    sudo python3 setup.py install

RUN \
      git clone https://github.com/CESNET/libyang.git && \
      git clone https://github.com/allena29/libyang-cffi.git && \
      git clone https://github.com/allena29/python-yang-voodoo.git /working

RUN \
      cd /working && \
      git checkout devel && \
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
      LIBYANG_INSTALL=system python3 setup.py install && \
      LIBYANG_INSTALL=system python3 setup.py bdist_wheel && \
      mv dist/*.whl /pkgs

RUN \
      cd /working && \
      git checkout devel && \
      LIBYANG_INSTALL=system python3 setup.py install && \
      LIBYANG_INSTALL=system python3 setup.py bdist_wheel && \
      mv dist/*.whl /pkgs 

ADD home_builder/ /home/builder 
WORKDIR /home/builder
USER builder


RUN \
     sudo chown builder /pkgs -R && \
     sudo chown builder /home/builder -R  && \
     cd /home/builder/libyang && \
     abuild checksum && \
     abuild -r && \
     cp /home/builder/packages/builder/x86_64/libyang-v1.0r3-r0.apk /pkgs
