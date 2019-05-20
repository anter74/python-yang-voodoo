#!/bin/bash

sysrepod
#sysrepo-plugind
# netopeer2-server

echo "Importing YANG"
cd /working/yang
./install-yang.sh


echo "Importing Initial Data"
cd /working/init-data
./init-xml.sh

echo "Starting subscribers"
cd /working/subscribers
./launch-subscribers.sh



echo "Ready"
cd /working/clients
set -euo pipefail

if [ -f "/builder" ]
then
  ./run-test.sh
fi
./interactive
/bin/bash
