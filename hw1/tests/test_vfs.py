"""Тесты загрузки виртуальной файловой системы из XML."""

import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from errors import InvalidVfs, VfsNotFound
from vfs_reader import get_vfs

VFS_DIR = Path(__file__).resolve().parent.parent / "vfs"


class TestVfsReader(unittest.TestCase):
    """Проверяет реальные примеры VFS и ошибки загрузки."""

    def test_minimal_vfs(self):
        """Минимальная VFS содержит только пустую корневую папку."""
        vfs = get_vfs(str(VFS_DIR / "minimal.xml"))
        self.assertEqual(vfs.name, "minimal")
        self.assertEqual(vfs.root_directory.name, "/")
        self.assertEqual(vfs.root_directory.directories, [])
        self.assertEqual(vfs.root_directory.files, [])

    def test_several_files_and_binary_content(self):
        """Текст, base64 и вложенная папка загружаются без потерь."""
        root = get_vfs(str(VFS_DIR / "several_files.xml")).root_directory
        files = {item.name: item for item in root.files}
        self.assertEqual(set(files), {"readme.txt", "notes.txt", "data.bin"})
        self.assertEqual(files["readme.txt"].content,
                         "Example VFS with several files.")
        self.assertEqual(files["data.bin"].encoding, "base64")
        self.assertEqual(files["data.bin"].content,
                         bytes([0, 1, 2, 3, 255, 254]))
        self.assertEqual(root.directories[0].name, "docs")
        self.assertEqual(root.directories[0].files[0].name, "guide.txt")

    def test_deep_directory_tree(self):
        """Вложенность папок и файлы в них сохраняются."""
        root = get_vfs(str(VFS_DIR / "deep.xml")).root_directory
        home = root.directories[0]
        student = home.directories[0]
        project = student.directories[0]
        self.assertEqual(
            [root.name, home.name, student.name, project.name],
            ["/", "home", "student", "project"],
        )
        subdirs = {
            directory.name: directory for directory in project.directories
        }
        self.assertEqual(set(subdirs), {"src", "docs"})
        self.assertEqual(subdirs["src"].files[0].content,
                         'print("Hello from VFS")')

    def test_missing_file(self):
        """Отсутствующий XML вызывает понятную ошибку."""
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "missing.xml"
            with self.assertRaises(VfsNotFound):
                get_vfs(str(path))

    def test_invalid_xml(self):
        """Повреждённый XML отклоняется парсером."""
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "broken.xml"
            path.write_text("<vfs><directory>", encoding="utf-8")
            with self.assertRaises(ET.ParseError):
                get_vfs(str(path))

    def test_missing_root_directory(self):
        """XML без корневой папки не считается VFS."""
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "no_root.xml"
            path.write_text("<vfs />", encoding="utf-8")
            with self.assertRaises(InvalidVfs):
                get_vfs(str(path))


if __name__ == "__main__":
    unittest.main()
