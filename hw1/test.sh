#!/bin/bash

cd "$(dirname "$0")" || exit
PYTHONPATH=src python3 -m unittest discover -s tests -v
