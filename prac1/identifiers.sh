#!/bin/bash

file="$1"

if [ $# -eq 0 ]; then
  echo "Не нашел переданных аргументов."
  exit 1
fi

if [ ! -f "$1" ]; then
  echo "$1 не является файлом."
  exit 1
fi

grep -o "[a-zA-Z_][a-zA-Z0-9_]*" $file | tr '\n' ' ' | sort -u
