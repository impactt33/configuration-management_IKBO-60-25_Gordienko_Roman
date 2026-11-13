#!/usr/bin/env bash
# Сценарии работы с локальным репозиторием. Результаты видны в терминале.
set -e
cd "$(dirname "$0")/.."

echo "Ветвление: A -> B==1.5, C; B -> D; C -> E"
bash run.sh --test-mode --repo examples/branching.json \
    --name A --version 1.0 --max-depth 2

echo "Глубина 0: только A"
bash run.sh --test-mode --repo examples/branching.json \
    --name A --version 1.0 --max-depth 0

echo "Глубина 1: A и его прямые зависимости"
bash run.sh --test-mode --repo examples/branching.json \
    --name A --version 1.0 --max-depth 1

echo "Фильтр B: остаётся A -> C -> E"
bash run.sh --test-mode --repo examples/branching.json \
    --name A --version 1.0 --filter B

echo "Общая зависимость: D доступен через A и через C"
bash run.sh --test-mode --repo examples/shared.json \
    --name A --version 1.0 --max-depth 4

echo "Цикл: A -> B -> C -> A"
bash run.sh --test-mode --repo examples/cycle.json \
    --name A --version 1.0 --max-depth 10

echo "Петля: S -> S"
bash run.sh --test-mode --repo examples/cycle.json \
    --name S --version 1.0

echo "Пакет D без зависимостей"
bash run.sh --test-mode --repo examples/branching.json \
    --name D --version 1.0

echo "OK: тестовый режим"
