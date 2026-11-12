#!/usr/bin/env bash
set -euo pipefail

hw2_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
project_dir="$(dirname -- "$hw2_dir")"

if [[ -n "${PYTHON:-}" ]]; then
    python_bin="$PYTHON"
elif [[ -x "$project_dir/.venv/bin/python" ]]; then
    python_bin="$project_dir/.venv/bin/python"
else
    python_bin="python3"
fi

export PYTHONPATH="$project_dir${PYTHONPATH:+:$PYTHONPATH}"
exec "$python_bin" -B -m hw2.run "$@"
