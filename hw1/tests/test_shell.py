"""Тесты разбора и выполнения команд из модуля shell."""

import unittest
from pathlib import Path

from errors import (
    CommandError, ExitRequest, MissingArguments, ParseError, TooManyArguments,
    UnclosedQuote, UnknownCommand,
)
from shell import Shell, parse_command
from vfs_reader import Directory, VFS, get_vfs


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

    def test_empty_quoted_arguments(self):
        """Пустой путь в кавычках сохраняется как отдельный аргумент."""
        self.assertEqual(parse_command('cd ""'), ["cd", ""])
        self.assertEqual(parse_command("cd ''"), ["cd", ""])

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

    def setUp(self):
        """Создаёт шелл без загруженной VFS."""
        self.shell = Shell(None)

    def test_simple_command(self):
        """Заглушка ls выводит имя и аргументы."""
        self.assertEqual(self.shell.execute("ls -l /home"), "ls: ['-l', '/home']")

    def test_unknown_command(self):
        """Неизвестная команда бросает UnknownCommand."""
        with self.assertRaises(UnknownCommand):
            self.shell.execute("ld -l /home")

    def test_empty_line(self):
        """Пустой ввод ничего не выводит."""
        self.assertEqual(self.shell.execute(""), "")

    def test_unclosed_quote(self):
        """Ошибка парсера пробрасывается из execute наружу."""
        with self.assertRaises(UnclosedQuote):
            self.shell.execute('ld -l "/home')

    def test_exit_with_parameters(self):
        """Команда exit с аргументами бросает TooManyArguments."""
        with self.assertRaises(TooManyArguments):
            self.shell.execute("exit 5")

    def test_exit(self):
        """Команда exit бросает ExitRequest."""
        with self.assertRaises(ExitRequest):
            self.shell.execute("exit")


class TestCd(unittest.TestCase):
    """Переходы внутри VFS и сохранение состояния при ошибках."""

    def setUp(self):
        """Загружает VFS с вложенными каталогами перед каждым тестом."""
        path = Path(__file__).resolve().parent.parent / "vfs" / "deep.xml"
        self.shell = Shell(get_vfs(str(path)))

    def test_absolute_and_relative_paths(self):
        """Абсолютные и относительные пути меняют текущий каталог."""
        self.assertEqual(self.shell.current_path, "/")
        self.assertEqual(self.shell.execute("cd /home/student"), "")
        self.assertEqual(self.shell.current_path, "/home/student")
        self.shell.execute("cd project/src")
        self.assertEqual(self.shell.current_path, "/home/student/project/src")

    def test_parent_and_current_directory(self):
        """Точки в пути обозначают текущий и родительский каталоги."""
        self.shell.execute("cd /home/student/project/src")
        self.shell.execute("cd ./../docs/.")
        self.assertEqual(self.shell.current_path, "/home/student/project/docs")

    def test_root_and_repeated_separators(self):
        """Повторные разделители пути и переход в корень поддерживаются."""
        self.shell.execute("cd //home///student/")
        self.assertEqual(self.shell.current_path, "/home/student")
        self.shell.execute("cd /")
        self.assertIs(self.shell.current_directory, self.shell.vfs.root_directory)

    def test_cannot_move_above_root(self):
        """Переход выше корня оставляет пользователя в корневом каталоге."""
        self.shell.execute("cd /home")
        self.shell.execute("cd ../../../../")
        self.assertEqual(self.shell.current_path, "/")

    def test_quoted_directory_name(self):
        """Имя каталога с пробелом передаётся в кавычках."""
        root = self.shell.vfs.root_directory
        root.directories.append(Directory("My Documents", root, [], []))
        self.shell.execute('cd "/My Documents"')
        self.assertEqual(self.shell.current_path, "/My Documents")

    def test_missing_directory_keeps_original_location(self):
        """Несуществующий путь не меняет текущий каталог."""
        self.shell.execute("cd /home")
        original = self.shell.current_directory
        with self.assertRaisesRegex(CommandError, "no such file or directory"):
            self.shell.execute("cd student/project/missing")
        self.assertIs(self.shell.current_directory, original)

    def test_file_in_path_is_rejected(self):
        """Переход в файл или через файл вызывает ошибку."""
        for path in ("/welcome.txt", "/home/student/notes.txt/.."):
            with self.subTest(path=path):
                with self.assertRaisesRegex(CommandError, "not a directory"):
                    self.shell.execute(f"cd {path}")
                self.assertEqual(self.shell.current_path, "/")

    def test_argument_errors(self):
        """Отсутствующий, пустой путь и лишние аргументы вызывают ошибки."""
        with self.assertRaises(MissingArguments):
            self.shell.execute("cd")
        with self.assertRaises(TooManyArguments):
            self.shell.execute("cd / /home")
        with self.assertRaisesRegex(CommandError, "empty path"):
            self.shell.execute('cd ""')
        self.assertEqual(self.shell.current_path, "/")

    def test_cd_without_vfs(self):
        """Переход без загруженной VFS вызывает понятную ошибку."""
        shell = Shell(None)
        self.assertEqual(shell.current_path, "/")
        with self.assertRaisesRegex(CommandError, "VFS is not loaded"):
            shell.execute("cd /")


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
        root = Directory("/", None, [], [])
        root.directories.append(Directory("My Documents", root, [], []))
        self.shell = Shell(VFS("test", root), self.logger)

    def test_command_is_logged(self):
        """Вызов команды записывается с именем и аргументами."""
        self.shell.execute('cd "My Documents"')
        self.assertEqual(self.logger.events, [("cd", ["My Documents"])])

    def test_unknown_command_is_logged(self):
        """Попытка вызвать неизвестную команду тоже записывается."""
        with self.assertRaises(UnknownCommand):
            self.shell.execute("foo bar")
        self.assertEqual(self.logger.events, [("foo", ["bar"])])

    def test_exit_is_logged(self):
        """Команда exit записывается до выхода."""
        with self.assertRaises(ExitRequest):
            self.shell.execute("exit")
        self.assertEqual(self.logger.events, [("exit", [])])

    def test_empty_line_is_not_logged(self):
        """Пустая строка и комментарий не записываются."""
        self.shell.execute("   # comment")
        self.assertEqual(self.logger.events, [])

    def test_parse_error_is_not_logged(self):
        """Строка с ошибкой разбора не записывается."""
        with self.assertRaises(UnclosedQuote):
            self.shell.execute('ls "abc')
        self.assertEqual(self.logger.events, [])

    def test_failed_cd_is_logged(self):
        """Неудачная попытка сменить каталог тоже записывается в лог."""
        with self.assertRaises(CommandError):
            self.shell.execute("cd /missing")
        self.assertEqual(self.logger.events, [("cd", ["/missing"])])


if __name__ == "__main__":
    unittest.main()
