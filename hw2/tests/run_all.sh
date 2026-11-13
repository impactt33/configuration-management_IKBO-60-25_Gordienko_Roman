#!/usr/bin/env bash
# Запустить все сценарии. --offline пропускает обращения к PyPI.
set -e
cd "$(dirname "$0")"

case "${1:-}" in
    ""|--offline) ;;
    --help|-h) echo "Использование: bash run_all.sh [--offline]"; exit 0 ;;
    *) echo "Использование: bash run_all.sh [--offline]"; exit 2 ;;
esac
if [ "$#" -gt 1 ]; then
    echo "Использование: bash run_all.sh [--offline]"
    exit 2
fi

bash test_mode.sh
bash test_load_order.sh
bash test_visualization.sh
bash test_errors.sh

if [ "${1:-}" != "--offline" ]; then
    bash test_pypi.sh
fi

echo "OK: все сценарии прошли"
