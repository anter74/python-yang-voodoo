#!/bin/sh

# This script uses the big dockerfile in builder to compile things from source
# with known versions. It then (crudely) creates a set of deb files, which this
# script extracts.
# The smaller deb file is used to create a minimal enviornemnt and installs
# the smaller deb file.
# Instead of 1.29GB for the full image we are closer to 250MB with this approach.
#


set pipefail -euo

echo "Building image and compiling everything...."
img=`docker build builder | tail -n 1 | sed -e's/Successfully built //'`
container=`docker run -i -d $img /bin/bash`

echo "Image $img, Container $container"
if [ -d artefacts ]
then
  rm -fr artefacts
fi

echo "Copying deb pacakge"


docker cp $container:/artefacts .
wget https://bootstrap.pypa.io/get-pip.py -O artefacts/get-pip.py
git clone https://github.com/allena29/python-yang-voodoo.git artefacts/working
docker stop $container

img=`docker build . | tail -n 1 | sed -e's/Successfully built //'`
echo "Built minimal development image"
docker tag $img allena29/yangvoodoo:devel

rm -fr artefacts
