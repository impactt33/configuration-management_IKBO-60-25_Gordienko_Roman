"""Тесты разбора и выполнения команд из модуля shell."""

import unittest

from shell import ExitRequest, ParseError, execute, parse_command


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
        """Неизвестная команда выдаёт сообщение об ошибке."""
        self.assertEqual(execute("ld -l /home"), "Command ld not found.")

    def test_empty_line(self):
        """Пустой ввод ничего не выводит."""
        self.assertEqual(execute(""), "")

    def test_unclosed_quote(self):
        """Ошибка парсера возвращается как сообщение."""
        self.assertEqual(execute('ld -l "/home'), 'Unclosed quote: "')

    def test_exit_with_parameters(self):
        """Команда exit с аргументами выдаёт ошибку."""
        self.assertEqual(execute("exit 5"), "exit: too many arguments.")

    def test_exit(self):
        """Команда exit бросает ExitRequest."""
        with self.assertRaises(ExitRequest):
            execute("exit")


if __name__ == "__main__":
    unittest.main()
