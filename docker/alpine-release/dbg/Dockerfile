FROM allena29/yangvoodoo:alpine-release-0.0.6.7-b

RUN apk add git libxml2-utils && \
    pip3 install -U ipython mock dill netmiko==2.4.2 && \
    mkdir /root/.ipython/ && \
    mkdir /root/.ipython/profile_default && \
    echo "c.Completer.use_jedi = False" >> /root/.ipython/profile_default/ipython_config.py  && \
    mkdir /logs

ARG YANGPATH
ENV YANGPATH /usr/yang
