"""Запись вызовов команд эмулятора в XML-лог."""

import getpass
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path


class XmlLogger:
    """XML-лог: держит дерево событий в памяти и сохраняет его в файл."""

    def __init__(self, path: str) -> None:
        """Загружает существующий лог или создаёт пустой.

        Raises:
            OSError: если файл не удаётся прочитать.
            ET.ParseError: если файл не является корректным XML.
        """
        self._abs_path = Path(path).absolute()
        if self._abs_path.exists():
            self.tree = ET.parse(self._abs_path)
        else:
            self.tree = ET.ElementTree(ET.Element("log"))
        self.root = self.tree.getroot()

    def log(self, command: str, arguments: list[str]) -> None:
        """Добавляет событие вызова команды и сохраняет лог."""
        timestamp = datetime.now().isoformat(timespec="seconds")
        event = ET.SubElement(self.root, "event")
        ET.SubElement(event, "datetime").text = timestamp
        ET.SubElement(event, "user").text = getpass.getuser()
        ET.SubElement(event, "command").text = command
        args = ET.SubElement(event, "args")
        for arg in arguments:
            ET.SubElement(args, "arg").text = arg
        self._save()

    def _save(self) -> None:
        """Перезаписывает файл лога целиком, создавая папку."""
        ET.indent(self.tree)
        self._abs_path.parent.mkdir(parents=True, exist_ok=True)
        self.tree.write(self._abs_path, encoding="utf-8", xml_declaration=True)
