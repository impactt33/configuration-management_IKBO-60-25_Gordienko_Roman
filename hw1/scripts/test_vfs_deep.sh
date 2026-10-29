#!/bin/bash
# Проверка VFS с папками глубиной более трёх уровней.

cd "$(dirname "$0")/.." || exit

echo "VFS deep: в окне имя VFS и команды стартового скрипта"
./run.sh --vfs vfs/deep.xml --script scripts/stage3_demo.txt
