FROM centos:7

RUN yum install -y gcc python3 curl git cmake python3-devel \
    pcre-devel make sudo wget openssl-devel bzip2-devel sqlite-devel \
    libffi-devel glibc-static pcre-static

RUN wget https://www.python.org/ftp/python/3.7.3/Python-3.7.3.tar.xz && \
    tar -xf Python-3.7.3.tar.xz

RUN cd Python-3.7.3 && \
    ./configure && \
    make install


WORKDIR /opt/dev

RUN \
      pip3 install wheel


RUN \
      # CHANGE VERSION HERE
      echo "0.0.7.1" >/version && \
      git clone https://github.com/allena29/libyang-cffi.git && \
      git clone https://github.com/allena29/python-yang-voodoo.git /working


RUN \
      cd /working && \
      mkdir /pkgs && \
      python3 setup.py bdist_wheel && \
      mv dist/*.whl /pkgs

RUN \
      cd /opt/dev && \
      cd libyang-cffi && \
      git pull && \
      git checkout master && \
      git submodule update --init --recursive && \
      python3 setup.py bdist_wheel && \
      mv dist/*.whl /pkgs



RUN \
      wget https://files.pythonhosted.org/packages/fa/aa/025a3ab62469b5167bc397837c9ffc486c42a97ef12ceaa6699d8f5a5416/bcrypt-3.1.7.tar.gz && \
      tar xvfz bcrypt-3.1.7.tar.gz && \
      cd bcrypt-3.1.7 && \
      python3 setup.py bdist_wheel && \
      python3 -m pip install dist/*.whl && \
      mv dist/*.whl /pkgs

RUN \
       tar cvpfz /pkgs/python-3.7-centos-7.tar.gz /usr/local/bin /usr/local/include/ /usr/local/lib
