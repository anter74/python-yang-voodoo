#!/bin/sh

# This script uses the big dockerfile in builder to compile things from source
# with known versions. It then (crudely) creates a set of deb files, which this
# script extracts.
# The smaller deb file is used to create a minimal enviornemnt and installs
# the smaller deb file.
# Instead of 1.29GB for the full image we are closer to 350MB with this approach.
# We have test harness things in place.

if [ $1 = "" ]
then
  echo "Provide a tag name"
  exit 1
fi
tag=$1

echo "TODO: build this image without sysrepo"


set pipefail -euo

echo "Building image and compiling everything...."
img=`docker build builder | tail -n 1 | sed -e's/Successfully built //'`
docker tag $img allena29/yangvoodoo:builder

container=`docker run -i -d $img /bin/bash`

echo "Image $img, Container $container"
if [ -d release/artefacts ]
then
  rm -fr release/artefacts
fi

echo "Copying deb pacakge"


docker cp $container:/artefacts release
wget https://bootstrap.pypa.io/get-pip.py -O release/artefacts/get-pip.py
if [ -d release/git-clone ]
then
  rm -fr release/git-clone
fi
git clone -b $tag https://github.com/allena29/python-yang-voodoo.git release/git-clone
docker stop $container

img=`docker build release | tail -n 1 | sed -e's/Successfully built //'`
echo "Built minimal development image"
docker tag $img allena29/yangvoodoo:release-$tag
