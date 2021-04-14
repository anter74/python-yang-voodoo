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
      pip3 install wheel


RUN \
      wget https://files.pythonhosted.org/packages/c4/43/3f1e7d742e2a7925be180b6af5e0f67d38de2f37560365ac1a0b9a04c015/lxml-4.4.1.tar.gz && \
      tar xvfz lxml-4.4.1.tar.gz && \
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
      wget https://files.pythonhosted.org/packages/fa/aa/025a3ab62469b5167bc397837c9ffc486c42a97ef12ceaa6699d8f5a5416/bcrypt-3.1.7.tar.gz && \
      tar xvfz bcrypt-3.1.7.tar.gz && \
      cd bcrypt-3.1.7 && \
      python3 setup.py bdist_wheel && \
      python3 -m pip install dist/*.whl && \
      mv dist/*.whl /pkgs

RUN \
      wget https://files.pythonhosted.org/packages/61/ab/2ac6dea8489fa713e2b4c6c5b549cc962dd4a842b5998d9e80cf8440b7cd/PyNaCl-1.3.0.tar.gz && \
      tar xvfz PyNaCl-1.3.0.tar.gz  && \
      cd PyNaCl-1.3.0 && \
      python3 setup.py bdist_wheel && \
      python3 -m pip install dist/*.whl && \
      mv dist/*.whl /pkgs

RUN \
      wget https://files.pythonhosted.org/packages/be/60/da377e1bed002716fb2d5d1d1cab720f298cb33ecff7bf7adea72788e4e4/cryptography-2.8.tar.gz && \
      tar xvfz cryptography-2.8.tar.gz && \
      cd cryptography-2.8 && \
      python3 setup.py bdist_wheel && \
      python3 -m pip install dist/*.whl && \
      mv dist/*.whl /pkgs

RUN \
      # CHANGE VERSION HERE
      echo "0.0.8.7" >/version && \
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
      git checkout v1.0.176 && \
      mkdir build && cd build && \
      cmake .. && \
      make -j6  && \
      make install && \
      ln -s /usr/local/lib64/*yang* /usr/local/lib

RUN \
      cd /working && \
      git checkout  devel && \
      LIBYANG_INSTALL=system python3 setup.py install


RUN \
      cd /opt/dev && \
      cd libyang-cffi && \
      git pull && \
      # CHANGE BRANCH HERE
      git checkout remove-true-from-datanode && \
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
     abuild -r

RUN \
     cp /home/builder/packages/builder/x86_64/libyang-v1.0.130r0-r0.apk /pkgs/libyang-v1.0.130.apk
