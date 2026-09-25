#!/bin/bash

file="$1"

if [ "$EUID" -ne 0 ]; then 
  echo "Запусти от sudo."
  exit 1
fi

if [ $# -eq 0 ]; then
  echo "Не нашел переданных аргументов."
  exit 1
fi

if [ ! -f "$1" ]; then
  echo "$1 не является файлом."
  exit 1
fi

start_file=$(head -n 1 "$file" | grep -o '^#!')

if [ -z "$start_file" ]; then
  echo "Это не bash script."
  exit 1
fi

dest="/usr/local/bin/$(basename "$file")"

cp "$file" "$dest"
chmod 755 "$dest"

echo "Success"
