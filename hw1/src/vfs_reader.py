"""Загрузка дерева виртуальной файловой системы из XML в память."""

from __future__ import annotations

import base64
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from random import paretovariate

from errors import InvalidVfs, VfsNotFound


@dataclass
class VFS:
    """Загруженная VFS с именем и корневой папкой."""

    name: str
    root_directory: Directory


@dataclass
class Directory:
    """Папка VFS с вложенными папками и файлами."""

    name: str
    parent: Directory | None
    directories: list[Directory]
    files: list[File]


@dataclass
class File:
    """Файл VFS: текст или декодированные двоичные данные."""

    name: str
    parent: Directory
    encoding: str
    content: str | bytes


def read_directory(element: ET.Element, parent: Directory | None = None) -> Directory:
    """Рекурсивно преобразует XML-папку в дерево объектов."""

    curr_directory = Directory(
        name=element.attrib["name"],
        directories=[],
        parent=parent,
        files=[]
    )

    for child in element:
        if child.tag == "directory":
            curr_directory.directories.append(read_directory(child, curr_directory))
        elif child.tag == "file":
            name = child.attrib["name"]
            encoding = child.attrib["encoding"]
            if encoding == "base64":
                content = base64.b64decode(child.text or "")
            else:
                content = child.text or ""

            curr_directory.files.append(File(
                name=name,
                parent=curr_directory,
                encoding=encoding,
                content=content
            ))

    return curr_directory


def get_vfs(path: str) -> VFS:
    """Читает XML по указанному пути и возвращает VFS в памяти."""

    abs_path = Path(path)

    if not abs_path.exists():
        raise VfsNotFound(path)

    tree = ET.parse(abs_path)
    root_tag = tree.getroot()
    root_dir = root_tag.find("directory")

    if root_dir is None:
        raise InvalidVfs(path)

    return VFS(abs_path.stem, root_directory=read_directory(root_dir))