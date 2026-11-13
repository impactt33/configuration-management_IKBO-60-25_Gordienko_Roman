"""Запись вызовов команд эмулятора в XML-лог."""

import getpass
import xml.etree.ElementTree as element_tree
from datetime import datetime
from pathlib import Path


class XmlLogger:
    """XML-лог: держит дерево событий в памяти и сохраняет его в файл."""

    def __init__(self, path: str) -> None:
        """Загружает существующий лог или создаёт пустой.

        Raises:
            OSError: если файл не удаётся прочитать.
            element_tree.ParseError: если файл не является корректным XML.
        """
        self._abs_path = Path(path).absolute()
        if self._abs_path.exists():
            self.tree = element_tree.parse(self._abs_path)
        else:
            self.tree = element_tree.ElementTree(element_tree.Element("log"))
        self.root = self.tree.getroot()

    def log(self, command: str, arguments: list[str]) -> None:
        """Добавляет событие вызова команды и сохраняет лог."""
        timestamp = datetime.now().isoformat(timespec="seconds")
        event = element_tree.SubElement(self.root, "event")
        element_tree.SubElement(event, "datetime").text = timestamp
        element_tree.SubElement(event, "user").text = getpass.getuser()
        element_tree.SubElement(event, "command").text = command
        args = element_tree.SubElement(event, "args")
        for arg in arguments:
            element_tree.SubElement(args, "arg").text = arg
        self._save()

    def _save(self) -> None:
        """Перезаписывает файл лога целиком, создавая папку."""
        element_tree.indent(self.tree)
        self._abs_path.parent.mkdir(parents=True, exist_ok=True)
        self.tree.write(self._abs_path, encoding="utf-8", xml_declaration=True)
