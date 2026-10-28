#!/bin/bash
# Проверка параметра --vfs: имя VFS в заголовке окна.
# На этапе 2 файл VFS не читается, из пути берётся только имя.
# Каждый вызов открывает окно, закройте его, чтобы перейти к следующему.

cd "$(dirname "$0")/.." || exit

echo "1. Без --vfs: в заголовке имя по умолчанию myvfs"
./run.sh

echo "2. --vfs vfs/minimal.xml: в заголовке minimal"
./run.sh --vfs vfs/minimal.xml

echo "3. Вложенные папки в пути: в заголовке только имя файла deep"
./run.sh --vfs vfs/levels/deep.xml
