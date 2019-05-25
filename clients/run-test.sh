#!/bin/bash


set -euo pipefail


pycodestyle ./
python3 -m unittest discover test/unit
python3 -m unittest discover test/integration
