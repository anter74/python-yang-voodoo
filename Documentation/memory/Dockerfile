FROM centos:7

RUN yum install -y gcc python3 curl git cmake python3-devel \
    pcre-devel make sudo wget openssl-devel bzip2-devel sqlite-devel \
    libffi-devel glibc-static pcre-static

RUN yum install -y gcc python3 curl git cmake python3-devel pcre-devel make rpm-build doxygen  make sudo wget openssl-devel bzip2-devel sqlite-devel libffi-devel gcc-c++

RUN yum install -y valgrind valgrind-devel

ARG PYTHON_VER=3.9.5
ARG PYTHON_OPTS=
# If we are missing python on the artefact server
RUN wget https://www.python.org/ftp/python/$PYTHON_VER/Python-$PYTHON_VER.tar.xz && \
    tar -xf Python-$PYTHON_VER.tar.xz

RUN cd Python-$PYTHON_VER && \
    ./configure $PYTHON_OPTS && \
    make install

WORKDIR /opt/dev

RUN \
      pip3 install wheel ipython


ENV GIT_BRANCH=master

RUN \
      # CHANGE VERSION HERE
      echo "0.0.9.0" >/version && \
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
      git submodule update --init --recursive 


RUN \
	cd /opt/dev/libyang-cffi/clib && \
        mkdir build && \
        cd build && \
        cmake  -g -D CMAKE_BUILD_TYPE:String="Debug" .. && \
        make  && \
        make install && \
        cd /opt/dev/libyang-cffi && \
        git checkout $GIT_BRANCH && \
	echo "/usr/local/lib64" > /etc/ld.so.conf.d/libyang.conf && \
        ldconfig && \
        LIBYANG_INSTALL=system python3 setup.py build --debug && \
        LIBYANG_INSTALL=system python3 setup.py install

RUN \
      mkdir /cleanpython && \
      rsync -avz /usr/local/bin /cleanpython/ && \
      rsync -avz /usr/local/include /cleanpython/ && \
      rsync -avz  --exclude='test/' --exclude='__pycache__/' /usr/local/lib /cleanpython/ && \
      cd /cleanpython && \
      tar cvpfz /pkgs/python-3.7-centos-7.tar.gz bin include lib

RUN \
	cd /working && \
	LIBYANG_INSTALL=system python3 setup.py install 

WORKDIR /vol
ENV YANGPATH=/working/yang
