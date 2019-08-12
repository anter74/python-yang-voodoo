FROM ubuntu:disco

# See the builder directory which compiles our dependencies from scratch.
# This is trying to build a minimal file and will just install those packages.

RUN \
      apt-get update && apt-get install -y \
      python3 \
      python3-distutils \
      libpcre3 \
      libpython3.7 

RUN \
    mkdir -p /root/.ipython/profile_default   && \
    echo "c.Completer.use_jedi = False" >/root/.ipython/profile_default/ipython_config.py && \
    echo "c.TerminalInteractiveShell.confirm_exit = False" >>/root/.ipython/profile_default/ipython_config.py

ADD artefacts /

RUN \
      dpkg -i /libyang*.deb && \
      rm -fr /*.deb && \
      ldconfig && \
      apt-get clean && \
      apt-get autoclean


RUN \
      python3 /get-pip.py && \
      rm -f /get-pip.py && \
      python3 -m pip install /libyang*.whl && \
      python3 -m pip install /yangvoodoo*.whl && \
      pip3 install ipython && \
      rm -fr /*.whl  && \
      rm -fr /*.tar.gz

STOPSIGNAL SIGTERM
WORKDIR /working
CMD /working
