"""Тесты разбора параметров командной строки из модуля main."""

import contextlib
import io
import unittest

from main import parse_args


class TestParseArgs(unittest.TestCase):
    """Тесты функции parse_args."""

    def test_no_arguments(self):
        """Без параметров все значения равны None."""
        args = parse_args([])
        self.assertEqual(
            (args.vfs, args.log, args.script), (None, None, None),
        )

    def test_all_arguments(self):
        """Все три параметра разбираются в любом порядке."""
        args = parse_args([
            "--script", "s.txt", "--vfs", "vfs/my.xml", "--log", "log.xml",
        ])
        self.assertEqual(args.vfs, "vfs/my.xml")
        self.assertEqual(args.log, "log.xml")
        self.assertEqual(args.script, "s.txt")

    def test_unknown_argument(self):
        """Неизвестный параметр завершает программу с ошибкой."""
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                parse_args(["--lgo", "log.xml"])

    def test_missing_value(self):
        """Параметр без значения завершает программу с ошибкой."""
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                parse_args(["--log"])


if __name__ == "__main__":
    unittest.main()
