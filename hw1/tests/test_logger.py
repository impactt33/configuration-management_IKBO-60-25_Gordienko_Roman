"""Тесты XML-логгера из модуля logger."""

import getpass
import tempfile
import unittest
import xml.etree.ElementTree as element_tree
from datetime import datetime
from pathlib import Path

from logger import XmlLogger


class TestXmlLogger(unittest.TestCase):
    """Тесты записи событий в XML-лог."""

    def create_log_path(self):
        """Создаёт временную папку, лог кладётся во вложенную logs/."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.path = Path(self.temp_dir.name) / "logs" / "session.xml"

    def read_events(self):
        """Читает все события из файла лога."""
        return element_tree.parse(self.path).getroot().findall("event")

    def test_no_file_before_first_event(self):
        """Пока нет событий, файл не создаётся."""
        self.create_log_path()
        XmlLogger(str(self.path))
        self.assertFalse(self.path.exists())

    def test_creates_missing_directory(self):
        """Папка для лога создаётся при первом событии."""
        self.create_log_path()
        XmlLogger(str(self.path)).log("ls", [])
        self.assertTrue(self.path.exists())

    def test_event_fields(self):
        """Событие содержит дату, пользователя, команду и аргументы."""
        self.create_log_path()
        XmlLogger(str(self.path)).log("cd", ["My Documents"])
        event = self.read_events()[0]
        timestamp = datetime.fromisoformat(event.find("datetime").text)
        self.assertIsInstance(timestamp, datetime)
        self.assertEqual(event.find("user").text, getpass.getuser())
        self.assertEqual(event.find("command").text, "cd")
        args = [arg.text for arg in event.iter("arg")]
        self.assertEqual(args, ["My Documents"])

    def test_events_in_one_session(self):
        """Все события одного запуска попадают в один файл по порядку."""
        self.create_log_path()
        logger = XmlLogger(str(self.path))
        logger.log("cd", ["a"])
        logger.log("ls", [])
        commands = [e.find("command").text for e in self.read_events()]
        self.assertEqual(commands, ["cd", "ls"])

    def test_appends_to_existing_log(self):
        """Повторный запуск дописывает события к старым."""
        self.create_log_path()
        XmlLogger(str(self.path)).log("cd", [])
        XmlLogger(str(self.path)).log("ls", ["-l"])
        commands = [e.find("command").text for e in self.read_events()]
        self.assertEqual(commands, ["cd", "ls"])

    def test_broken_file(self):
        """Повреждённый файл лога вызывает ParseError."""
        self.create_log_path()
        self.path.parent.mkdir()
        self.path.write_text("<log><event>", encoding="utf-8")
        with self.assertRaises(element_tree.ParseError):
            XmlLogger(str(self.path))


if __name__ == "__main__":
    unittest.main()
