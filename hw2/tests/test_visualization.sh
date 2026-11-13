#!/usr/bin/env bash
# Создание картинок из локального репозитория. Браузер не открывается.
set -e
cd "$(dirname "$0")/.."

echo "Картинка с ветвлением"
bash run.sh --test-mode --repo examples/branching.json \
    --name A --version 1.0 --format d2 \
    --output output/tests/visualization/branching.svg
test -s output/tests/visualization/branching.svg

echo "Картинка с фильтром B"
bash run.sh --test-mode --repo examples/branching.json \
    --name A --version 1.0 --filter B --format d2 \
    --output output/tests/visualization/filtered.svg
test -s output/tests/visualization/filtered.svg

echo "Картинка с циклом"
bash run.sh --test-mode --repo examples/cycle.json \
    --name A --version 1.0 --max-depth 10 --format d2 \
    --output output/tests/visualization/cycle.svg
test -s output/tests/visualization/cycle.svg

echo "OK: картинки в hw2/output/tests/visualization/"
