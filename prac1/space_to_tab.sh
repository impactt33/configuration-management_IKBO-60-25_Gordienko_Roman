#!/bin/bash

input_file="$1"
output_file="$2"

if [ $# -ne 2 ]; then
  echo "Usage: $0 input_file output_file"
  exit 1
fi

if [ ! -f "$input_file" ]; then
  echo "$input_file is not a file."
  exit 1
fi

if [ "$input_file" -ef "$output_file" ]; then
  echo "Input and output must be different files."
  exit 1
fi

sed 's/    /\t/g' "$input_file" > "$output_file"
