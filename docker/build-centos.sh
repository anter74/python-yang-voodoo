#!/bin/sh

experiment="1"
#
# ps -ef | grep "python -m http.server 8080" 2>/dev/null
# if [ $? != 0 ]
# then
#   echo "HTTP Server needed to server python image (copy it from the builder container)"
#   echo "And then ensure it's served from /docker-tools"
#   exit 1;
# fi


rm -fr centos-release/examples

# This version is minimal
if [ "$experiment" = "1" ]
then
  echo "Experimental"
  cd ../
  rm -fr build
  rm -fr dist
  python3 setup.py build bdist_wheel
  cd docker
  rm -fr centos-release/templates
  rm -fr centos-release/yang

fi

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

if [ "$experiment" = "1" ]
then
  cp ../dist/*.whl centos-release/pkgs
  cp -dR ../examples centos-release
  cp -dR ../yang centos-release
  cp -dR ../templates centos-release
fi
rm -fr centos-release/pkgs/*.tar.gz


img=`docker build --squash centos-release | tail -n 1 | sed -e's/Successfully built //'`
docker tag $img allena29/yangvoodoo:centos-release
