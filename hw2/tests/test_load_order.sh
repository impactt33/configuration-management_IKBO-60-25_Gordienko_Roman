#!/usr/bin/env bash
# Вывод порядка загрузки на нескольких понятных графах.
set -e
cd "$(dirname "$0")/.."

echo "Ветвление. Ожидается: D, B, E, C, A"
bash run.sh --test-mode --repo examples/branching.json \
    --name A --version 1.0 --max-depth 10 --format order

echo "Общая зависимость. Ожидается: E, D, C, B, A"
bash run.sh --test-mode --repo examples/shared.json \
    --name A --version 1.0 --max-depth 10 --format order

echo "Фильтр B. Ожидается: E, C, A"
bash run.sh --test-mode --repo examples/branching.json \
    --name A --version 1.0 --filter B --format order

echo "Глубина 1. Ожидается: B, C, A"
bash run.sh --test-mode --repo examples/branching.json \
    --name A --version 1.0 --max-depth 1 --format order

echo "Пакет без зависимостей. Ожидается: D"
bash run.sh --test-mode --repo examples/branching.json \
    --name D --version 1.0 --format order

echo "OK: порядок загрузки"
