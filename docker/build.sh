#!/bin/sh

# This script uses the big dockerfile in builder to compile things from source
# with known versions. It then (crudely) creates a set of deb files, which this
# script extracts.
# The smaller deb file is used to create a minimal enviornemnt and installs
# the smaller deb file.
# Instead of 1.29GB for the full image we are closer to 350MB with this approach.
# We have test harness things in place.


set pipefail -euo

echo "Building image and compiling everything...."
img=`docker build builder | tail -n 1 | sed -e's/Successfully built //'`
docker tag $img allena29/yangvoodoo:builder

container=`docker run -i -d $img /bin/bash`

echo "Image $img, Container $container"
if [ -d devel/artefacts ]
then
  rm -fr devel/artefacts
fi

echo "Copying deb pacakge"

docker cp $container:/artefacts devel
wget https://bootstrap.pypa.io/get-pip.py -O devel/artefacts/get-pip.py
git clone -b master https://github.com/allena29/python-yang-voodoo.git devel/artefacts/working
docker stop $container


rm -fr devel/artefacts/*standalone*

img=`docker build devel | tail -n 1 | sed -e's/Successfully built //'`
echo "Built minimal development image"
docker tag $img allena29/yangvoodoo:devel
