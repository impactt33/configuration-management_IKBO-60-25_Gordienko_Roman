"""Тесты разбора и выполнения команд из модуля shell."""

import unittest

from errors import (
    ExitRequest, ParseError, TooManyArguments, UnclosedQuote, UnknownCommand,
)
from shell import execute, parse_command


class TestParseCommand(unittest.TestCase):
    """Тесты разбора командной строки."""

    def test_simple_command(self):
        """Слова разделяются пробелами."""
        self.assertEqual(parse_command("ls -l /home"), ["ls", "-l", "/home"])

    def test_double_quotes(self):
        """Двойные кавычки объединяют слова."""
        self.assertEqual(parse_command('cd "a b"'), ["cd", "a b"])

    def test_single_quotes(self):
        """Одинарные кавычки объединяют слова."""
        self.assertEqual(parse_command("cd 'a b'"), ["cd", "a b"])

    def test_quote_in_the_middle(self):
        """Закрывающая кавычка не завершает аргумент."""
        self.assertEqual(parse_command('cd "a b"cd'), ["cd", "a bcd"])

    def test_extra_space_symbols(self):
        """Лишние пробелы и табуляция вне кавычек пропускаются."""
        test_string = 'cd "a   b"      c  \t d'
        self.assertEqual(parse_command(test_string), ["cd", "a   b", "c", "d"])

    def test_empty_line(self):
        """Пустая строка даёт пустой список."""
        self.assertEqual(parse_command(""), [])

    def test_comment(self):
        """Всё после # отбрасывается."""
        self.assertEqual(parse_command("cd abc # abc"), ["cd", "abc"])

    def test_comment_in_quotes(self):
        """Символ # внутри кавычек не начинает комментарий."""
        self.assertEqual(parse_command('cd "abc # abc"'), ["cd", "abc # abc"])

    def test_unclosed_quote(self):
        """Незакрытая кавычка - ошибка."""
        with self.assertRaises(ParseError):
            parse_command('ls "abc')


class TestExecute(unittest.TestCase):
    """Тесты выполнения команд."""

    def test_simple_command(self):
        """Заглушка ls выводит имя и аргументы."""
        self.assertEqual(execute("ls -l /home"), "ls: ['-l', '/home']")

    def test_unknown_command(self):
        """Неизвестная команда бросает UnknownCommand."""
        with self.assertRaises(UnknownCommand):
            execute("ld -l /home")

    def test_empty_line(self):
        """Пустой ввод ничего не выводит."""
        self.assertEqual(execute(""), "")

    def test_unclosed_quote(self):
        """Ошибка парсера пробрасывается из execute наружу."""
        with self.assertRaises(UnclosedQuote):
            execute('ld -l "/home')

    def test_exit_with_parameters(self):
        """Команда exit с аргументами бросает TooManyArguments."""
        with self.assertRaises(TooManyArguments):
            execute("exit 5")

    def test_exit(self):
        """Команда exit бросает ExitRequest."""
        with self.assertRaises(ExitRequest):
            execute("exit")


class TestErrorMessages(unittest.TestCase):
    """Тексты ошибок, которые видит пользователь."""

    def test_unknown_command_message(self):
        """Сообщение о неизвестной команде содержит её имя."""
        self.assertEqual(str(UnknownCommand("foo")), "foo: unknown command.")

    def test_too_many_arguments_message(self):
        """Сообщение о лишних аргументах содержит имя команды."""
        self.assertEqual(
            str(TooManyArguments("exit")), "exit: too many arguments.",
        )

    def test_unclosed_quote_message(self):
        """Сообщение о незакрытой кавычке содержит саму кавычку."""
        self.assertEqual(str(UnclosedQuote('"')), 'Unclosed quote: "')


class FakeLogger:
    """Подмена XmlLogger: запоминает события вместо записи в файл."""

    def __init__(self):
        """Создаёт пустой список событий."""
        self.events = []

    def log(self, command, arguments):
        """Запоминает событие вызова команды."""
        self.events.append((command, arguments))


class TestExecuteLogging(unittest.TestCase):
    """Тесты записи вызовов команд в лог."""

    def setUp(self):
        """Создаёт подменный логгер перед каждым тестом."""
        self.logger = FakeLogger()

    def test_command_is_logged(self):
        """Вызов команды записывается с именем и аргументами."""
        execute('cd "My Documents"', self.logger)
        self.assertEqual(self.logger.events, [("cd", ["My Documents"])])

    def test_unknown_command_is_logged(self):
        """Попытка вызвать неизвестную команду тоже записывается."""
        with self.assertRaises(UnknownCommand):
            execute("foo bar", self.logger)
        self.assertEqual(self.logger.events, [("foo", ["bar"])])

    def test_exit_is_logged(self):
        """Команда exit записывается до выхода."""
        with self.assertRaises(ExitRequest):
            execute("exit", self.logger)
        self.assertEqual(self.logger.events, [("exit", [])])

    def test_empty_line_is_not_logged(self):
        """Пустая строка и комментарий не записываются."""
        execute("   # comment", self.logger)
        self.assertEqual(self.logger.events, [])

    def test_parse_error_is_not_logged(self):
        """Строка с ошибкой разбора не записывается."""
        with self.assertRaises(UnclosedQuote):
            execute('ls "abc', self.logger)
        self.assertEqual(self.logger.events, [])


if __name__ == "__main__":
    unittest.main()
