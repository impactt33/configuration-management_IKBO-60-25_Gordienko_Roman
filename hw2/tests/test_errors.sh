#!/usr/bin/env bash
# Проверяем ожидаемые ошибки по коду завершения. Сообщения видны в терминале.
set -e
cd "$(dirname "$0")/.."

expect_error() {
    local expected="$1"
    shift
    local actual=0
    bash run.sh "$@" || actual=$?
    if [ "$actual" -ne "$expected" ]; then
        echo "FAIL: ожидался код $expected, получен $actual"
        exit 1
    fi
}

echo "Нет обязательных аргументов: ожидается код 2"
expect_error 2

echo "Отрицательная глубина: ожидается код 2"
expect_error 2 --name A --version 1.0 --max-depth -1

echo "Неверная версия: ожидается код 2"
expect_error 2 --name A --version invalid

echo "Нет файла: ожидается код 1"
expect_error 1 --test-mode --repo examples/missing.json \
    --name A --version 1.0

echo "Нет пакета Z: ожидается код 1"
expect_error 1 --test-mode --repo examples/branching.json \
    --name Z --version 1.0

echo "Нет версии 99.0: ожидается код 1"
expect_error 1 --test-mode --repo examples/branching.json \
    --name A --version 99.0

echo "У цикла нет строгого порядка: ожидается код 1"
expect_error 1 --test-mode --repo examples/cycle.json \
    --name A --version 1.0 --max-depth 10 --format order

echo "OK: ожидаемые ошибки обработаны"
