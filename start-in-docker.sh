#!/bin/bash


echo "Ready"
cd /working
if [ -f "/builder" ]
then
  ./run-test.sh
fi

if [ $? = 0 ]
then
  ./interactive
fi
/bin/bash
