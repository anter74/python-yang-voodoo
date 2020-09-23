#!/bin/sh

# This version is minimal


set pipefail -euo

echo "Building image and compiling everything...."
img=`docker build centos-builder | tail -n 1 | sed -e's/Successfully built //'`
docker build --tag allena29/yangvoodoo:centos-builder centos-builder

container=`docker run --rm -i -d allena29/yangvoodoo:centos-builder  /bin/bash`

echo "Image $img, Container $container"

echo "Copying pacakges"
rm -fr centos-release/pkgs/*.whl
rm -fr centos-release/pkgs/*.tar.gz

docker cp $container:/pkgs centos-release
docker stop $container
rm -fr centos-release/pkgs/*.tar.gz

img=`docker build --squash centos-release | tail -n 1 | sed -e's/Successfully built //'`
docker tag $img allena29/yangvoodoo:centos-release
