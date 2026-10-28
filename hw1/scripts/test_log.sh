#!/bin/bash
# Проверка параметра --log: XML-лог вызовов команд.
# Каждый вызов открывает окно, закройте его, чтобы перейти к следующему.

cd "$(dirname "$0")/.." || exit
mkdir -p logs
rm -f logs/test_log.xml

echo "1. Новый лог: введите несколько команд и закройте окно"
./run.sh --log logs/test_log.xml
echo "Содержимое logs/test_log.xml:"
cat logs/test_log.xml 2>/dev/null || echo "(файла нет: команды не вводились)"
echo

echo "2. Тот же лог ещё раз: события скрипта добавляются к старым"
./run.sh --log logs/test_log.xml --script scripts/no_errors.txt
echo "Содержимое logs/test_log.xml:"
cat logs/test_log.xml
echo

echo "3. Повреждённый лог: сообщение Log error, эмулятор работает без лога"
printf '<log><event>' > logs/broken.xml
./run.sh --log logs/broken.xml
