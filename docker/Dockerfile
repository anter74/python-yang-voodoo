FROM ubuntu:cosmic

RUN \
      apt-get update && apt-get install -y \
      # general tools
      git \
      vim \
      curl \
      gnupg \
      apt-transport-https \
      python3 \
      python3-pip

RUN \
      apt-get update && apt-get install -y \
      cmake \
      build-essential \
      supervisor \
      libpcre3-dev \
      pkg-config \
      libavl-dev \
      libev-dev \
      libprotobuf-c-dev \
      protobuf-c-compiler \
      libssl-dev \
      swig \
      python-dev \
      python3-dev \
      libcurl4-openssl-dev \
      libxslt-dev \
      libxml2-dev \
      libtool \
      libtool-bin \
      python-setuptools \
      libreadline-dev \
      python-libxml2 \
      libprotobuf-dev && \
      apt-get install -y libtool libtool-bin libxml2-dev libxslt1-dev libcurl4-openssl-dev xsltproc python-setuptools cmake zlib1g-dev libssl-dev pkg-config libreadline-dev && \ 
      apt-get install -y bison libboost-thread-dev libboost-thread1.67-dev autoconf automake screen && \
      apt-get install -y libffi-dev || echo 'livffi-dev does not exist'

RUN \ 
    pip3 install ipython ncclient

# add netconf user
RUN \
    adduser --system netconf && \
    echo "netconf:netconf" | chpasswd

# generate ssh keys for netconf user
RUN \
    mkdir -p /home/netconf/.ssh && \
    ssh-keygen -A && \
    ssh-keygen -t dsa -P '' -f /home/netconf/.ssh/id_dsa && \
    cat /home/netconf/.ssh/id_dsa.pub > /home/netconf/.ssh/authorized_keys

# use /opt/dev as working directory
RUN mkdir /opt/dev
WORKDIR /opt/dev

# libyang
RUN \
      cd /opt/dev && \
      git clone https://github.com/CESNET/libyang.git && \
      cd libyang && \
      git checkout 85d09f3bdf5ea01ea2e01deb384b2b0dde057e3f && \
      git checkout v0.16-r3 && \
      mkdir build && cd build && \
      cmake .. && \
      make -j6  && \
      make install && \
      ldconfig

    

# sysrepo
RUN \
      cd /opt/dev && \
      git clone https://github.com/sysrepo/sysrepo.git && \
      cd sysrepo && \
      # git checkout 724a62fa830df7fcb2736b1ec41b320abe5064d2 && \
      git checkout v0.7.7 && \
      mkdir build_python3 && \
      cd build_python3 && \
      cmake -DREPOSITORY_LOC=/sysrepo -DGEN_PYTHON_VERSION=3 .. && \
      make -j6 && \
      make install && \
      ldconfig 

RUN \ 
      pip3 install libyang 

# Optional build a deb
RUN \ 
      mkdir ~/sysrepo-python-bundle && \
      cd / && \
      tar cvpf /tmp/working.tar /usr/local /sysrepo  /usr/lib/python3/dist-packages/*sysrepo* && \
      cd ~/sysrepo-python-bundle && \
      tar xvf /tmp/working.tar && \
      rm -fr usr/local/games && \
      rm -fr usr/local/lib/python2.7 && \
      tar cvpf /tmp/libyang.tar usr/local/lib/python3.6/dist-packages/*libyang* && \
      rm -fr usr/local/lib/python3.6 && \
      tar xvf /tmp/libyang.tar && \
      mkdir ~/sysrepo-python-bundle/DEBIAN && \
      echo "Package: sysrepo-libyang-python-bundle" >~/sysrepo-python-bundle/DEBIAN/control && \
      echo "Version: 0.7.7-04" >>~/sysrepo-python-bundle/DEBIAN/control && \
      echo "Architecture: amd64" >>~/sysrepo-python-bundle/DEBIAN/control && \
      echo "Depends: libev4,libprotobuf-c1" >>~/sysrepo-python-bundle/DEBIAN/control && \
      echo "Maintainer: allena29@noreply.user.github.com" >>~/sysrepo-python-bundle/DEBIAN/control && \
      echo "Description: sysrepo/libyang-python bundle without netconf support for local use." >>~/sysrepo-python-bundle/DEBIAN/control && \
      echo "#!/bin/sh" >~/sysrepo-python-bundle/DEBIAN/postinst && \
      echo "ldconfig" >>~/sysrepo-python-bundle/DEBIAN/postinst && \
      echo "touch /tmp/pkginstall" >>~/sysrepo-python-bundle/DEBIAN/postinst && \
      chmod 755 ~/sysrepo-python-bundle/DEBIAN/postinst && \
      dpkg --build ~/sysrepo-python-bundle && \
      mv /root/sysrepo-python-bundle.deb /sysrepo-python-bundle.0.7.7-04.amd64.deb


RUN \
    apt-get clean && \
    apt-get autoclean && \
    rm -fr /opt/dev


ENV EDITOR vim
EXPOSE 830
STOPSIGNAL SIGTERM
WORKDIR /sysrepo
