FROM allena29/yangvoodoo:devel

RUN pip3 install jupyter

# Websockets version with ttyd
#RUN apt-get update && \
#    apt-get install -y vim-runtime cmake g++ pkg-config git \
#    libwebsockets-dev libjson-c-dev libssl-dev telnet inetutils-ping tmux


#RUN git clone https://github.com/tsl0922/ttyd.git && \
#    cd ttyd && mkdir build && cd build && \
#    cmake .. && \
#    make && make install

RUN apt-get update && \
    apt-get install -y vim-runtime  \
    telnet inetutils-ping tmux shellinabox

RUN useradd jungle && \
    mkdir /home/jungle && \
    chown jungle:jungle /home/jungle && \
    echo "jungle:jupyter" | chpasswd && \
    usermod --shell /bin/bash jungle && \
    mkdir /run/sshd

RUN   apt-get clean && \
      apt-get autoclean && \
      mkdir /home/jungle/yangvoodoo && \
      cp /working/clients/interactive /home/jungle/yangvoodoo && \
      ln -s /working/yang /home/jungle/yang && \
      rm -fr /working/.git && \
      chown jungle:jungle /working -R

RUN mkdir /home/jungle/.jupyter && \
    echo '{"NotebookApp": {"password": "sha1:7d1f963e0784:985dc93fbb444b72e24068f9922da1ed4587dce6"}}' >/home/jungle/.jupyter/jupyter_notebook_config.json && \ 
    echo "set-option -g default-shell /bin/bash" >/home/jungle/.tmux.conf  && \
    mkdir -p /home/jungle/.ipython/profile_default   && \
    echo "c.Completer.use_jedi = False" >/home/jungle/.ipython/profile_default/ipython_config.py && \
    echo "c.TerminalInteractiveShell.confirm_exit = False" >>/home/jungle/.ipython/profile_default/ipython_config.py && \
    mkdir -p /home/jungle/.jupyter && \
    echo '{ "keys": { "command": { "unbind": [ "x", "c", "r" ], "bind": { "c": "jupyter-notebook:restart-kernel-and-clear-output", "k": "jupyter-notebook:shutdown-kernel", "r": "jupyter-notebook:run-all-cells" } } } ' >/home/jungle/.jupyter/nb_config

COPY start-notebook.sh /

ADD notebook /home/jungle/notebook 

RUN chown jungle:jungle /home/jungle -R

WORKDIR /home/jungle
CMD /start-notebook.sh

EXPOSE 8888 8889
