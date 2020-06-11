FROM centos:7


ADD pkgs /pkgs

RUN tar xvfz /pkgs/python-3.7-centos-7.tar.gz && \
    rm -fr /pkgs/python*.tar.gz

RUN pip3 install lxml==4.4.1 cffi==1.12.3 PyNaCl==1.3.0 cryptography==2.8


RUN pip3 install /pkgs/*.whl 

