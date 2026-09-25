#!/bin/bash

dir="$1"

if [ $# -ne 1 ]; then
  echo "params error"
  exit 1
fi

if [ ! -d "$dir" ]; then
  echo "not a directory"
  exit 1
fi

find "$dir" -maxdepth 1 -type f -size 0
