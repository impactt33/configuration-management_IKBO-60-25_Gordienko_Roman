#!/bin/bash

dir="$1"

if [ ! -d "$dir" ]; then 
  echo "not a directory."
  exit 1
fi

line="$(find "$dir" -type f -exec md5sum {} + | sort | uniq -w 32 --all-repeated=separate)"

if [ -z "$line" ]; then
  echo "No duplicates"
else
  echo "$line"
fi
