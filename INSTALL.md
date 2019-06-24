
# Local development environment (without Docker)

## Dependencies

#### Linux

```
see Dockerfile - see below for sysrepo install.
```

#### Mac OSX

Tested with Mojave 10.14.3

```bash
xcode-select --install
brew install cmake        # tested with version 3.14.3
brew install protobuf-c   # tested with version 1.3.1.2
brew install libev        # tested with version 4.24
brew install pcre         # tested with version 8.43
wget http://prdownloads.sourceforge.net/swig/swig-3.0.12.tar.gz
tar xvfz swig-3.0.12.tar.gz
cd swig-3.0.12
./configure
make && sudo make install
cd ../
git clone --branch v1.0-r2  https://github.com/CESNET/libyang.git
cd libyang
mkdir build && cd build
cmake ..
make && sudo make install
cd ../
git clone https://github.com/sysrepo/libredblack.git
cd libredblack
./configure && make && sudo make install
```

## pyenv/virtualenv

The git clone has a `.python-version` file which is only important if pyenv is used for a virtual environment. To create a virtual-env the following will clone and add to a bash shell.

```bash

git clone https://github.com/pyenv/pyenv.git ~/.pyenv
PATH=~/.pyenv/bin:$PATH
  eval "$(pyenv init -)"
export PYENV_ROOT="$HOME/.pyenv"
git clone https://github.com/pyenv/pyenv-virtualenv.git ~/.pyenv/plugins/pyenv-virtualenv
  # For MAC-OSX Mojave
  export PYTHON_CONFIGURE_OPTS="--enable-framework"
  export LDFLAGS="-L/usr/local/opt/zlib/lib -L/usr/local/opt/sqlite3/lib"
  export CPPFLAGS="-I/usr/local/opt/zlib/include -I/usr/local/opt/sqlite3/include"
  export CFLAGS="-I$(xcrun --show-sdk-path)/usr/include"
pyenv install 3.7.3
eval "$(pyenv virtualenv-init -)"
pyenv virtualenv 3.7.3 yang-voodoo-373
pip install -r requirements.lock

echo 'export PYENV_ROOT="$HOME/.pyenv"' >>~/.bashrc
echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >>~/.bashrc
echo 'eval "$(pyenv init -)"' >>~/.bashrc
echo 'eval "$(pyenv virtualenv-init -)"' >>~/.bashrc
echo 'export PS1="{\[\033[36m\]\u@\[\033[36m\]\h} \[\033[33;1m\]\w\[\033[m\] \$ "' >>~/.bashrc
echo 'export PYENV_VIRTUALENV_DISABLE_PROMPT=1' >>~/.bashrc

```

## libyang/sysrepo and python bindings


The following instructions install sysrepo bindings within a pyenv environment. If not using pyenv then follow the simpler steps from the docker file.

For MAC-OSX libpython3.7.dylib, for Linux libpython3.7m.a

```bash
git clone --branch=v0.7.7 https://github.com/sysrepo/sysrepo.git
cd sysrepo
echo "3.7.3/envs/yang-voodoo-373" >.python-version
sed  -e 's/unset/#/' -i.bak swig/CMakeLists.txt
mkdir build
cd build
cmake -DPYTHON_EXECUTABLE=~/.pyenv/versions/yang-voodoo-373/bin/python3  -DPYTHON_LIBRARY=~/.pyenv/versions/3.7.3/lib/libpython3.7.dylib  -DPYTHON_INCLUDE_DIR=~/.pyenv/versions/3.7.3/include/python3.7m  -DGEN_LUA_BINDINGS=0 -DREPOSITORY_LOC=/sysrepo -DGEN_PYTHON_VERSION=3 ..
make && sudo make install

# Libyang
cd /tmp
git clone https://github.com/allena29/libyang-cffi
cd libyang-cffi
echo "3.7.3/envs/yang-voodoo-373" >.python-version
LIBYANG_INSTALL=system python3 setup.py install
```



# Rapsbian Install

Raspbian includes an old version python, swig, and libboost-thread1 is an older version- these notes are a combination of the documentation above and the Dockerfile.

```
sudo apt-get install libprotobuf-c1 libev4 libavl1 curl openssh-client git screen cmake build-essential supervisor libpcre3-dev pkg-config libavl-dev libev-dev libprotobuf-c-dev protobuf-c-compiler libssl-dev libcurl4-openssl-dev libxslt-dev libxml2-dev libtool libtool-bin libreadline-dev libprotobuf-dev zlib1g-dev bison libboost-thread1.62-dev autoconf automake libffi-dev vim git tmux

git clone https://github.com/pyenv/pyenv.git ~/.pyenv
PATH=~/.pyenv/bin:$PATH
eval "$(pyenv init -)"
export PYENV_ROOT="$HOME/.pyenv"

git clone https://github.com/pyenv/pyenv-virtualenv.git ~/.pyenv/plugins/pyenv-virtualenv
pyenv install 3.7.3
eval "$(pyenv virtualenv-init -)"
pyenv virtualenv 3.7.3 yang-voodoo-373


echo 'export PYENV_ROOT="$HOME/.pyenv"' >>~/.bashrc
echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >>~/.bashrc
echo 'eval "$(pyenv init -)"' >>~/.bashrc
echo 'eval "$(pyenv virtualenv-init -)"' >>~/.bashrc
echo 'export PS1="{\[\033[36m\]\u@\[\033[36m\]\h} \[\033[33;1m\]\w\[\033[m\] \$ "' >>~/.bashrc
echo 'export PYENV_VIRTUALENV_DISABLE_PROMPT=1' >>~/.bashrc


adduser --system netconf && \
echo "netconf:netconf" | chpasswd
mkdir -p /home/netconf/.ssh && \
ssh-keygen -A && \
ssh-keygen -t dsa -P '' -f /home/netconf/.ssh/id_dsa && \
cat /home/netconf/.ssh/id_dsa.pub > /home/netconf/.ssh/authorized_keys


git clone https://github.com/CESNET/libyang.git && \
cd libyang && \
git checkout v0.16-r3 && \
mkdir build && cd build && \
cmake .. && \
make -j6  && \
make install && \
sudo ldconfig

cd ~/
wget https://sourceforge.net/projects/swig/files/swig/swig-3.0.12/swig-3.0.12.tar.gz/download -O swig-3.0.12.tar.gz
tar xvfz swig-3.0.12.tar.gz
cd swig-3.0.12
./configure
make
sudo make install
sudo ldconfig

cd ~/
git clone --branch=v0.7.7 https://github.com/sysrepo/sysrepo.git
cd sysrepo
echo "3.7.3/envs/yang-voodoo-373" >.python-version
sed  -e 's/unset/#/' -i.bak swig/CMakeLists.txt
mkdir build
cd buil7
cmake -DPYTHON_EXECUTABLE=~/.pyenv/versions/yang-voodoo/bin/python3  -DPYTHON_LIBRARY=~/.pyenv/versions/3.7.3/lib/libpython3.7m.a  -DPYTHON_INCLUDE_DIR=~/.pyenv/versions/3.7.3/include/python3.7m  -DGEN_LUA_BINDINGS=0 -DREPOSITORY_LOC=/sysrepo -DGEN_PYTHON_VERSION=3 ..
make && sudo make install

cd ~/
git clone https://git.libssh.org/projects/libssh.git libssh && \
cd libssh && \
git checkout libssh-0.8.7 && \
mkdir build && cd build && \
cmake .. && \
make -j6 && \
sudo make install
sudo ldconfig

cd ~/
git clone https://github.com/CESNET/libnetconf2.git && \
cd libnetconf2 && mkdir build && cd build && \
git checkout v0.12-r1 && \
cmake .. && \
make -j6 && \
sudo make install && \
sudo ldconfig


git clone https://github.com/CESNET/Netopeer2.git && \
cd Netopeer2 && \
# git checkout d3ae5423847cbfc67c844ad19288744701bd47a4 && \
git checkout v0.7-r1 && \
# This commit fixes keystored method signature (original-xpath missing)
git checkout 6db56863fcac3fc21c18835576314a75ceea1267 && \
cd keystored && mkdir build && cd build && \
cmake .. && \
make -j6
cd ~/Netopeer2/server
mkdir build
cd build
cmake ..
make
sudo make install

cd ~/
git clone https://github.com/allena29/libyang-cffi.git
LIBYANG_INSTALL=system python3 setup.py install
```


# Oven test

```
cd ~/
sudo /usr/local/bin/sysrepod -d -l 4
```
