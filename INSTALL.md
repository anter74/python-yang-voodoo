
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
pyenv install 3.6.7
eval "$(pyenv virtualenv-init -)"
pyenv virtualenv 3.6.7 yang-voodoo
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

```bash
git clone --branch=v0.7.7 https://github.com/sysrepo/sysrepo.git
cd sysrepo
echo "3.6.7/envs/yang-voodoo" >.python-version
sed  -e 's/unset/#/' -i.bak swig/CMakeLists.txt
mkdir build
cd build
cmake -DPYTHON_EXECUTABLE=~/.pyenv/versions/yang-voodoo/bin/python3  -DPYTHON_LIBRARY=~/.pyenv/versions/3.6.7/lib/libpython3.6.dylib  -DPYTHON_INCLUDE_DIR=~/.pyenv/versions/3.6.7/include/python3.6m  -DGEN_LUA_BINDINGS=0 -DREPOSITORY_LOC=/sysrepo -DGEN_PYTHON_VERSION=3 ..
make && sudo make install

# Libyang
cd /tmp
git clone https://github.com/allena29/libyang-cffi
cd libyang-cffi
LIBYANG_INSTALL=system python3 setup.py install
```
