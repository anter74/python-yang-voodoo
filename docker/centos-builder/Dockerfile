FROM centos:7

RUN yum install -y gcc python3 curl git cmake python3-devel \
    pcre-devel make sudo wget bzip2-devel sqlite-devel \
    libffi-devel glibc-static pcre-static zlib-devel

RUN wget --no-check-certificate https://www.openssl.org/source/openssl-1.1.1q.tar.gz && tar -xf openssl-1.1.1q.tar.gz


RUN cd openssl-1.1.1q && \
    ./config --prefix=/usr/local/openssl-1-1-1q --openssldir=/usr/local/openssl-1-1-1q && \
    make && \
    make install

RUN wget https://www.python.org/ftp/python/3.10.5/Python-3.10.5.tar.xz && \
    tar -xf Python-3.10.5.tar.xz

RUN cd Python-3.10.5 && \
    ./configure -C --with-openssl=/usr/local/openssl-1-1-1q --with-openssl-rpath=auto --with-ensurepip=install && \
    make install



WORKDIR /opt/dev

RUN \
      pip3 install wheel


ENV GIT_BRANCH=support-attrs

RUN \
      # CHANGE VERSION HERE
      echo "0.0.13" >/version && \
      git clone https://github.com/allena29/libyang-cffi.git && \
      git clone https://github.com/allena29/python-yang-voodoo.git /working


RUN \
      cd /working && \
      mkdir /pkgs && \
      git checkout $GIT_BRANCH && \
      python3 setup.py bdist_wheel && \
      mv dist/*.whl /pkgs

RUN \
      cd /opt/dev && \
      cd libyang-cffi && \
      git pull && \
      git checkout $GIT_BRANCH && \
      git submodule update --init --recursive && \
      python3 setup.py bdist_wheel && \
      mv dist/*.whl /pkgs



RUN \
      wget https://files.pythonhosted.org/packages/e8/36/edc85ab295ceff724506252b774155eff8a238f13730c8b13badd33ef866/bcrypt-3.2.2.tar.gz && \
      tar xvfz bcrypt-3.2.2.tar.gz && \
      cd bcrypt-3.2.2 && \
      python3 setup.py bdist_wheel && \
      python3 -m pip install dist/*.whl && \
      mv dist/*.whl /pkgs

#RUN \
#      curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh && \
#      pip3 install setuprools_rust


#RUN \
#      wget https://files.pythonhosted.org/packages/89/d9/5fcd312d5cce0b4d7ee8b551a0ea99e4ea9db0fdbf6dd455a19042e3370b/cryptography-37.0.4.tar.gz && \
#	tar xvfz cryptography-37.0.4.tar.gz  && \
#	cd cryptography-37.0.4 && \
#	export LDFLAGS="-L/usr/local/openssl-1-1-1q/lib" && \
#	export CFLAGS="-I/usr/local/openssl-1-1-1q/include" && \
#	export PATH="$HOME/.cargo/bin:$PATH"


RUN \
      mkdir /cleanpython && \
      rsync -avz /usr/local/bin /cleanpython/ && \
      rsync -avz /usr/local/openssl-1-1-1q /cleanpython/ && \
      rsync -avz /usr/local/include /cleanpython/ && \
      rsync -avz  --exclude='test/' --exclude='__pycache__/' /usr/local/lib /cleanpython/ && \
      cd /cleanpython && \
      tar cvpfz /pkgs/python-3.10.5-openssl-1-1-1q-centos-7.tar.gz bin include lib openssl-1-1-1q
