#!/bin/sh

# This version is minimal


set pipefail -euo

echo "Building image and compiling everything...."
img=`docker build builder | tail -n 1 | sed -e's/Successfully built //'`
docker tag $img allena29/yangvoodoo:builder

container=`docker run -i -d $img /bin/bash`

echo "Image $img, Container $container"
if [ -d minimal/artefacts ]
then
  rm -fr minimal/artefacts
fi

echo "Copying deb pacakge"

docker cp $container:/artefacts minimal
wget https://bootstrap.pypa.io/get-pip.py -O minimal/artefacts/get-pip.py
git clone -b devel https://github.com/allena29/python-yang-voodoo.git minimal/artefacts/working
docker stop $container


rm -fr minimal/artefacts/*.tar

img=`docker build minimal | tail -n 1 | sed -e's/Successfully built //'`
echo "Built minimal development image"
docker tag $img allena29/yangvoodoo:libyang-only
