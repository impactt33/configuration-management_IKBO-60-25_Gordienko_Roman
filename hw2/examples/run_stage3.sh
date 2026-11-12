#!/usr/bin/env bash
set -euo pipefail

examples_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
hw2_dir="$(dirname -- "$examples_dir")"

run_example() {
    local title="$1" repository="$2"
    shift 2
    printf '\n%s\n' "$title"
    bash "$hw2_dir/run.sh" --test-mode \
        --repo "$examples_dir/$repository.json" --version 1.0 "$@"
}

run_example "Ветвление и выбор B==1.5" branching --name A --max-depth 2
run_example "Только корень" branching --name A --max-depth 0
run_example "Только прямые зависимости" branching --name A --max-depth 1
run_example "Исключение B вместе с его веткой" branching \
    --name A --max-depth 3 --filter b
run_example "Цикл A -> B -> C -> A" cycle --name A --max-depth 10
run_example "Петля S -> S" cycle --name S --max-depth 10
run_example "Общая зависимость D в двух ветках" shared \
    --name A --max-depth 4
run_example "Пакет без зависимостей" branching --name D --max-depth 3
