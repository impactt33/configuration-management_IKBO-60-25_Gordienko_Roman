#!/bin/bash
# Проверка всех параметров вместе: --vfs, --log и --script.

cd "$(dirname "$0")/.." || exit
mkdir -p logs
rm -f logs/test_all.xml

echo "VFS minimal в заголовке, скрипт выполняется, команды пишутся в лог"
./run.sh --vfs vfs/minimal.xml --log logs/test_all.xml \
    --script scripts/no_errors.txt
echo "Содержимое logs/test_all.xml:"
cat logs/test_all.xml
echo
