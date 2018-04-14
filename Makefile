.PHONY: unittest

PYBIND := $(shell PYTHONPATH=../../confvillain /usr/bin/env python -c 'import pyangbind; import os; print ("{}/plugin".format(os.path.dirname(pyangbind.__file__)))')
PWD := $(shell pwd)

all:	pyang yin unittest

# TODO: need to discover the name of the yang file
pyang:
	PYTHONPATH=$(PYTHONPATH):../pyconfhoard pyang --plugindir $(PYBIND) --use-xpathhelper -f pybind -o binding.py brewerslab.yang

# TODO: remove hardcoding of the ynag file
yin:
	pyang -f yin -o schema.yin brewerslab.yang

unittest:
	nose2 -s test -t python -v --with-coverage --coverage-report html
