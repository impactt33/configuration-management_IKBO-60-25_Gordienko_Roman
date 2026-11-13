"""Проверки локального формата репозитория и его ошибок."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from hw2.main.data.file_dependencies_collector import FileDependenciesCollector
from hw2.main.domain.exceptions import (
    PackageNotFoundError, RepositoryFileError, VersionNotFoundError,
)


class TestFileDependenciesCollector(unittest.TestCase):
    """Создаёт временные репозитории только внутри hw2/tests."""

    def prepare_repository(self):
        """Изолирует каждый пример в отдельном каталоге."""
        directory = TemporaryDirectory(dir=Path(__file__).parent)
        self.addCleanup(directory.cleanup)
        self.path = Path(directory.name) / "repository with spaces.json"

    def write(self, data):
        """Записывает JSON и открывает его настоящим сборщиком."""
        self.path.write_text(json.dumps(data), encoding="utf-8")
        return FileDependenciesCollector(self.path)

    def test_versions_and_requirements_are_read_without_http(self):
        """Выбирается запрошенная версия; список не разделяется с клиентом."""
        self.prepare_repository()
        collector = self.write({
            "A": {"1.0": ["B>=1,<2"], "2.0": []},
            "B": {"1.5": []},
        })
        requirements = collector.get_pypi_dependencies_for_package(
            str(self.path), "A", "1.0.0",
        )
        self.assertEqual(requirements, ["B>=1,<2"])
        requirements.clear()
        self.assertEqual(
            collector.get_pypi_dependencies_for_package("", "A", "1.0"),
            ["B>=1,<2"],
        )
        self.assertEqual(
            collector.get_available_versions_of_package("", "A"),
            ["1.0", "2.0"],
        )

    def test_missing_package_and_release_have_domain_errors(self):
        """Отсутствующий пакет отличается от отсутствующей версии."""
        self.prepare_repository()
        collector = self.write({"A": {"1.0": []}})
        with self.assertRaisesRegex(PackageNotFoundError, "B"):
            collector.get_available_versions_of_package("", "B")
        with self.assertRaisesRegex(VersionNotFoundError, "A==2.0"):
            collector.get_pypi_dependencies_for_package("", "A", "2.0")

    def test_missing_file_is_reported(self):
        """Ошибка открытия содержит путь репозитория."""
        self.prepare_repository()
        with self.assertRaisesRegex(RepositoryFileError, "repository"):
            FileDependenciesCollector(self.path)

    def test_invalid_json_and_encoding_are_reported(self):
        """Ошибка формата не выходит наружу как JSONDecodeError."""
        self.prepare_repository()
        for content in (b"{", b"\xff"):
            with self.subTest(content=content):
                self.path.write_bytes(content)
                with self.assertRaises(RepositoryFileError):
                    FileDependenciesCollector(self.path)

    def test_invalid_graph_structures_are_rejected(self):
        """Отклоняются неверные имена, версии и списки зависимостей."""
        self.prepare_repository()
        invalid = [
            [], {}, {"lower": {"1.0": []}}, {"A1": {"1.0": []}},
            {"А": {"1.0": []}}, {"A": []}, {"A": {}},
            {"A": {"bad": []}}, {"A": {"1.0": [], "1.0.0": []}},
            {"A": {"1.0": "B"}}, {"A": {"1.0": [1]}},
            {"A": {"1.0": ["B>="]}}, {"A": {"1.0": ["b"]}},
            {"A": {"1.0": ["B @ https://example.invalid/b.whl"]}},
        ]
        for data in invalid:
            with self.subTest(data=data):
                with self.assertRaises(RepositoryFileError):
                    self.write(data)


if __name__ == "__main__":
    unittest.main()
