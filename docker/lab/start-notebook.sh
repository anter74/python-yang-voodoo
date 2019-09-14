#!/bin/sh

# It should be possible to start sysrepod/subscriber/plugins and netopeer2 as jungle without having to
# resort to always running it - this should be kinder on resources for low-end machiens.
# /working/start-in-docker.sh &
#sleep 1

# Get environment variable and reset password
jupyterpass=`python3 -c "from notebook.auth import passwd;import os;print(passwd(os.environ['LAB_TOKEN']))"`
echo "{\"NotebookApp\": {\"password\": \"$jupyterpass\"}}" >/home/jungle/.jupyter/jupyter_notebook_config.json
echo "jungle:$LAB_TOKEN" | chpasswd

shellinaboxd --port=8889 --disable-ssl -b
#screen -dmS ttyd ttyd -p 8889:8889 /bin/bash

su - jungle  -c "jupyter notebook --no-browser --allow-root --ip=0.0.0.0 /home/jungle/notebook"
