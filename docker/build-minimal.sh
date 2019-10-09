#!/bin/sh

# This version is minimal


set pipefail -euo

echo "Building image and compiling everything...."
img=`docker build alpine-builder | tail -n 1 | sed -e's/Successfully built //'`
docker tag $img allena29/yangvoodoo:alpine-builder

container=`docker run -i -d $img /bin/bash`

echo "Image $img, Container $container"

echo "Copying apk pacakges"
rm -fr alpine-release/pkgs/*.whl

docker cp $container:/pkgs alpine-release
docker stop $container

img=`docker build --squash alpine-release | tail -n 1 | sed -e's/Successfully built //'`
docker tag $img allena29/yangvoodoo:alpine-release
