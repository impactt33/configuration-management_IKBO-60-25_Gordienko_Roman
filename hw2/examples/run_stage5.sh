#!/usr/bin/env bash
set -euo pipefail

examples_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
hw2_dir="$(dirname -- "$examples_dir")"

for package in httpx:0.28.1 requests:2.32.3 rich:13.9.4; do
    name="${package%%:*}"
    version="${package#*:}"
    bash "$hw2_dir/run.sh" --name "$name" --version "$version" \
        --max-depth 100 --format d2 --output "$hw2_dir/output/$name.svg" "$@"
done
