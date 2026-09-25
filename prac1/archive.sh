#!/bin/bash

dir="$1"
tag="$2"
archive_name="$3"

if [ ! -d "$dir" ]; then
  echo "not a directory."
  exit 1
fi

if [ -z "$tag" ]; then
  echo "no parameter"
  exit 1
fi

if [ -z "$archive_name" ]; then
  archive_name="default"
fi


mapfile -t found < <(find "$dir" -type f -name "*.${tag}")


if [ "${#found[@]}" -eq 0 ]; then
  echo "No ${tag} files in this dir."
  exit 0
fi


tar -cvf "${archive_name}.tar" "${found[@]}"
