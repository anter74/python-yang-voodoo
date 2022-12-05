FROM centos:7

ENV YANGPATH=/yang

RUN curl http://192.168.3.1:8080/docker-tools/python-3.10.8-openssl-1-1-1q-centos-7.tar.gz | tar xvfz - -C /usr/local

ADD pkgs /pkgs

RUN pip3 install lxml==4.8.0 cffi==1.15.0 PyNaCl==1.5.0 cryptography==2.8 ipython==8.3.0 tornado==6.2
#RUN pip3 install lxml==4.8.0 cffi==1.15.0 PyNaCl==1.5.0
# RUN pip3 install lxml==4.8.0 cffi==1.15.0 PyNaCl==1.5.0 cryptography==2.8
# centos 7 and cryptography >= 3 depends on modern rust build tools.
# perhaps one day

RUN pip3 install /pkgs/*.whl

ADD examples /examples
ADD yang /yang
ADD templates /templates
