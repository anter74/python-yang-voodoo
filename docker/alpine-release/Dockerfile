FROM alpine:3.10.0

RUN apk add python3 libxml2 libxslt py3-setuptools libffi

ADD pkgs /tmp/pkgs

RUN \
    mv /tmp/pkgs/builder-5d715690.rsa.pub /etc/apk/keys && \
    apk add /tmp/pkgs/libyang-v1.0r3-r0.apk && \
    pip3 install dictdiffer==0.8.0 Jinja2==2.10.1 pycparser==2.19 MarkupSafe==1.1.1 && \
    python3 -m pip install /tmp/pkgs/*.whl 
