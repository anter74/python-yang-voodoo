#!/bin/bash

overall=0

echo ""
echo "LINT Checks.."
pycodestyle ./
if [ $? != 0 ]
then
  exit 1;
fi


echo ""
echo "Unit tests.. (Core Set)"
python3 -m unittest discover test/unitcore
if [ $? != 0 ]
then
  exit 1;
fi


echo ""
echo "Unit tests.. (Extended Set)"
python3 -m unittest discover test/unit
if [ $? != 0 ]
then
  exit 1;
fi


echo ""
echo "Integration tests.."
python3 -m unittest discover test/integration
if [ $? != 0 ]
then
  exit 1;
fi
