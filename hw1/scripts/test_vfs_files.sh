#!/bin/bash
# Проверка VFS с несколькими файлами, папкой и двоичными данными.

cd "$(dirname "$0")/.." || exit

echo "VFS several_files: в окне имя VFS и команды стартового скрипта"
./run.sh --vfs vfs/several_files.xml --script scripts/stage3_demo.txt
