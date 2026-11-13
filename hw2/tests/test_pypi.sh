#!/usr/bin/env bash
# Обычный режим: получить зависимости из PyPI и сохранить три картинки.
set -e
cd "$(dirname "$0")/.."

echo "PyPI: httpx"
bash run.sh --name httpx --version 0.28.1 --format d2 \
    --output output/tests/pypi/httpx.svg
test -s output/tests/pypi/httpx.svg

echo "PyPI: requests"
bash run.sh --name requests --version 2.32.3 --format d2 \
    --output output/tests/pypi/requests.svg
test -s output/tests/pypi/requests.svg

echo "PyPI: rich"
bash run.sh --name rich --version 13.9.4 --format d2 \
    --output output/tests/pypi/rich.svg
test -s output/tests/pypi/rich.svg

echo "OK: картинки в hw2/output/tests/pypi/"
