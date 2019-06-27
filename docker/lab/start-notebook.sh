#!/bin/sh

/working/start-in-docker.sh &
sleep 1

# Get environment variable and reset password
jupyterpass=`python3 -c "from notebook.auth import passwd;import os;print(passwd(os.environ['LAB_TOKEN']))"`
echo "{\"NotebookApp\": {\"password\": \"$jupyterpass\"}}" >/home/jungle/.jupyter/jupyter_notebook_config.json
echo "jungle:$LAB_TOKEN" | chpasswd

cat <<__EOF >/.white-on-black.css
#vt100 #cursor.bright {
  background-color: white;
  color:            black;
}

#vt100 #scrollable {
  color:            #ffffff;
  background-color: #000000;
}

#vt100 #scrollable.inverted {
  color:            #000000;
  background-color: #ffffff;
}

#vt100 .ansi15 {
  color:            #000000;
}

#vt100 .bgAnsi0 {
  background-color: #ffffff;
}#vt100 #cursor.bright {
  background-color: white;
  color:            black;
}

#vt100 #scrollable {
  color:            #ffffff;
  background-color: #000000;
}

#vt100 #scrollable.inverted {
  color:            #000000;
  background-color: #ffffff;
}

#vt100 .ansi15 {
  color:            #000000;
}

#vt100 .bgAnsi0 {
  background-color: #ffffff;
}
__EOF

shellinaboxd --port=8889 --disable-ssl -b 
#screen -dmS ttyd ttyd -p 8889:8889 /bin/bash

su - jungle  -c "jupyter notebook --no-browser --allow-root --ip=0.0.0.0 /home/jungle/notebook"
