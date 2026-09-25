#!/bin/bash

grep -v '^#' /etc/protocols | awk '{print $2, $1}' | sort -nr | head -n 5
