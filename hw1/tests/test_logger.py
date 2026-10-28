"""Тесты XML-логгера из модуля logger."""

import getpass
import tempfile
import unittest
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

from logger import XmlLogger


class TestXmlLogger(unittest.TestCase):
    """Тесты записи событий в XML-лог."""

    def setUp(self):
        """Создаёт временную папку, лог кладётся во вложенную logs/."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.path = Path(self.temp_dir.name) / "logs" / "session.xml"

    def tearDown(self):
        """Удаляет временную папку вместе с логом."""
        self.temp_dir.cleanup()

    def read_events(self):
        """Читает все события из файла лога."""
        return ET.parse(self.path).getroot().findall("event")

    def test_no_file_before_first_event(self):
        """Пока нет событий, файл не создаётся."""
        XmlLogger(str(self.path))
        self.assertFalse(self.path.exists())

    def test_creates_missing_directory(self):
        """Папка для лога создаётся при первом событии."""
        XmlLogger(str(self.path)).log("ls", [])
        self.assertTrue(self.path.exists())

    def test_event_fields(self):
        """Событие содержит дату, пользователя, команду и аргументы."""
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
        logger = XmlLogger(str(self.path))
        logger.log("cd", ["a"])
        logger.log("ls", [])
        commands = [e.find("command").text for e in self.read_events()]
        self.assertEqual(commands, ["cd", "ls"])

    def test_appends_to_existing_log(self):
        """Повторный запуск дописывает события к старым."""
        XmlLogger(str(self.path)).log("cd", [])
        XmlLogger(str(self.path)).log("ls", ["-l"])
        commands = [e.find("command").text for e in self.read_events()]
        self.assertEqual(commands, ["cd", "ls"])

    def test_broken_file(self):
        """Повреждённый файл лога вызывает ParseError."""
        self.path.parent.mkdir()
        self.path.write_text("<log><event>", encoding="utf-8")
        with self.assertRaises(ET.ParseError):
            XmlLogger(str(self.path))


if __name__ == "__main__":
    unittest.main()
