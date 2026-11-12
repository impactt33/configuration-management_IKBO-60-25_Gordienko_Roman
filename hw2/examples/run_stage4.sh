#!/usr/bin/env bash
set -euo pipefail

examples_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
hw2_dir="$(dirname -- "$examples_dir")"

for repository in branching shared; do
    printf '\nПорядок для %s\n' "$repository"
    bash "$hw2_dir/run.sh" --test-mode \
        --repo "$examples_dir/$repository.json" --name A --version 1.0 \
        --max-depth 10 --format order
done

printf '\nПакет без зависимостей\n'
bash "$hw2_dir/run.sh" --test-mode --repo "$examples_dir/branching.json" \
    --name D --version 1.0 --format order

printf '\nЦикл: ожидается ошибка, строгого порядка нет\n'
if bash "$hw2_dir/run.sh" --test-mode --repo "$examples_dir/cycle.json" \
    --name A --version 1.0 --max-depth 10 --format order; then
    printf 'Ошибка: цикл был принят как корректный порядок\n' >&2
    exit 1
else
    status=$?
    [[ "$status" -eq 1 ]]
fi
