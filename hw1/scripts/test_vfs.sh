#!/bin/bash
# Проверка минимальной VFS и ошибок загрузки.
# Каждый вызов открывает окно; закройте его для перехода к следующему.

cd "$(dirname "$0")/.." || exit

echo "1. Пустая VFS: в заголовке имя minimal"
./run.sh --vfs vfs/minimal.xml --script scripts/stage3_demo.txt

echo "2. Несуществующий XML: в окне сообщение VFS error"
./run.sh --vfs vfs/missing.xml

echo "3. Неверный формат: в окне сообщение VFS error"
./run.sh --vfs scripts/no_errors.txt
