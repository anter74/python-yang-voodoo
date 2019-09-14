FROM ubuntu:disco

# See the builder directory which compiles our dependencies from scratch.
# This is trying to build a minimal file and will just install those packages.

RUN \
      apt-get update && apt-get install -y \
      python3 \
      python3-distutils \
      screen \
      libpython3.7

RUN \
    mkdir -p /root/.ipython/profile_default   && \
    echo "c.Completer.use_jedi = False" >/root/.ipython/profile_default/ipython_config.py && \
    echo "c.TerminalInteractiveShell.confirm_exit = False" >>/root/.ipython/profile_default/ipython_config.py

ADD artefacts /

RUN \
      dpkg -i /*standalone*.deb && \
      rm -fr /*.deb && \
      apt-get clean && \
      apt-get autoclean


RUN \
      python3 /get-pip.py && \
      rm -f /get-pip.py && \
      pip3 install lxml jinja2 dictdiffer six asn1crypto

ADD git-clone/.colour git-clone/.black git-clone/interactive /working/
ADD git-clone/yang /working/yang

EXPOSE 830 5000
STOPSIGNAL SIGTERM
WORKDIR /working
