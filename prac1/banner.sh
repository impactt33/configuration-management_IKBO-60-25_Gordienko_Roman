#!/bin/bash

text="$1"
dashes="+"

for (( i = 0; i < ${#text} + 2; i++ )); do
  dashes="${dashes}-"
done
dashes="${dashes}+"

echo "$dashes"
echo "| $text |"
echo "$dashes"
