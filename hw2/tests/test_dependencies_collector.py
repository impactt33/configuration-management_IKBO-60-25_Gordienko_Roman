"""Проверки выбора файлов PyPI и связки сборщика с BFS без сети."""

import unittest
from unittest.mock import Mock

import httpx

from hw2.core.exceptions import HttpError
from hw2.core.http_client import HttpClient
from hw2.main.domain.dependencies_tree_builder import DependenciesTreeBuilder
from hw2.main.data.external_api.dependencies_collector import (
    DependenciesCollector,
)
from hw2.main.domain.entities.exception_cause import ExceptionCause
from hw2.main.domain.exceptions import VersionNotFoundError


def distribution_file(filename, metadata=True):
    """Создаёт запись файла искусственного Simple API."""
    return {
        "filename": filename,
        "url": f"https://example.invalid/files/{filename}",
        "core-metadata": metadata,
    }


class TestDependenciesCollector(unittest.TestCase):
    """Проверяет нормализацию и выбор файлов опубликованной версии."""

    def setUp(self):
        """Подменяет только HTTP, сохраняя настоящий код сборщика."""
        self.http = Mock(spec=HttpClient)
        self.collector = DependenciesCollector(self.http)
        self.repo = "example.invalid/simple"

    def select(self, name, version, files):
        """Передаёт сборщику искусственный список файлов."""
        self.http.get.return_value = httpx.Response(
            200, json={"files": files},
        )
        return self.collector._request_for_package_files(
            self.repo, name, version,
        )

    def test_hyphenated_name_matches_wheel(self):
        """Дефис в имени проекта соответствует подчёркиванию в wheel."""
        wheel = distribution_file("magic_filter-1.0.12-py3-none-any.whl")

        selected = self.select("magic-filter", "1.0.12", [wheel])

        self.assertEqual(selected, wheel)

    def test_typing_extensions_name_matches_wheel(self):
        """Имена зависимостей со знаком '-' принимаются из Requires-Dist."""
        wheel = distribution_file("typing_extensions-4.15.0-py3-none-any.whl")

        selected = self.select("typing-extensions", "4.15.0", [wheel])

        self.assertEqual(selected, wheel)

    def test_name_case_and_separators_are_normalized(self):
        """Регистр, точки и подчёркивания не меняют идентичность проекта."""
        wheel = distribution_file("my_package-1.0-py3-none-any.whl")

        selected = self.select("My.Package", "1.0", [wheel])

        self.assertEqual(selected, wheel)
        self.assertEqual(
            self.http.get.call_args.args[0],
            "https://example.invalid/simple/my-package/",
        )

    def test_equivalent_release_versions_match(self):
        """Версии 1.0 и 1.0.0 сравниваются по правилам PEP 440."""
        wheel = distribution_file("package-1.0.0-py3-none-any.whl")

        self.assertEqual(self.select("package", "1.0", [wheel]), wheel)

    def test_wheel_build_tag_is_supported(self):
        """Номер сборки wheel не становится частью версии пакета."""
        wheel = distribution_file("package-1.0-2-py3-none-any.whl")

        self.assertEqual(self.select("package", "1.0", [wheel]), wheel)

    def test_sdist_version_excludes_archive_extension(self):
        """Суффикс .tar.gz не входит в версию исходного архива."""
        archive = distribution_file("my-package-1.0.tar.gz")

        self.assertEqual(
            self.select("my-package", "1.0", [archive]), archive,
        )

    def test_zip_sdist_is_supported(self):
        """Исходные архивы .zip также разбираются без расширения в версии."""
        archive = distribution_file("package-1.0.zip")

        self.assertEqual(self.select("package", "1.0", [archive]), archive)

    def test_invalid_filenames_are_skipped(self):
        """Повреждённая запись не мешает найти корректный файл релиза."""
        wheel = distribution_file("package-1.0-py3-none-any.whl")
        files = [
            {}, {"filename": None}, {"filename": 123},
            distribution_file("invalid.whl"),
            distribution_file("package-invalid.tar.gz"), wheel,
        ]

        self.assertEqual(self.select("package", "1.0", files), wheel)

    def test_wheel_is_preferred_over_sdist(self):
        """При доступных метаданных обоих файлов выбирается wheel."""
        archive = distribution_file("package-1.0.tar.gz")
        wheel = distribution_file("package-1.0-py3-none-any.whl")

        self.assertEqual(
            self.select("package", "1.0", [archive, wheel]), wheel,
        )

    def test_file_with_core_metadata_is_preferred(self):
        """Предпочтение получает файл с заявленными метаданными."""
        first = distribution_file("package-1.0-1-py3-none-any.whl", False)
        second = distribution_file("package-1.0-2-py3-none-any.whl")

        self.assertEqual(
            self.select("package", "1.0", [first, second]), second,
        )

    def test_missing_version_error_identifies_package(self):
        """Сообщение ошибки содержит имя и запрошенную версию."""
        wheel = distribution_file("package-1.0-py3-none-any.whl")

        with self.assertRaisesRegex(VersionNotFoundError, "package.*2.0"):
            self.select("package", "2.0", [wheel])

    def test_http_error_is_preserved(self):
        """Ошибка HTTP не заменяется ошибкой выбора файла."""
        self.http.get.side_effect = HttpError(
            status=404, url="https://example.invalid/simple/missing/",
        )

        result = self.collector._request_for_package_files(
            self.repo, "missing", "1.0",
        )

        self.assertIsInstance(result, ExceptionCause)
        self.assertEqual(result.status_code, 404)

    def test_repository_url_can_include_scheme(self):
        """Готовая схема URL не дублируется при создании адреса проекта."""
        self.assertEqual(
            self.collector._create_simple_api_supported_pypi_url(
                "https://example.invalid/simple/", "My_Package",
            ),
            "https://example.invalid/simple/my-package/",
        )


class TestCollectorWithBFS(unittest.IsolatedAsyncioTestCase):
    """Проверяет обход через настоящий сборщик с ответами HTTP из памяти."""

    async def test_bfs_loads_dependencies_with_normalized_wheel_names(self):
        """Граф проходит через имена magic-filter и typing-extensions."""
        projects = {
            "aiogram": ("3.31.0", "aiogram", [
                "magic-filter>=1,<2", "typing-extensions>=4",
            ]),
            "magic-filter": ("1.0.12", "magic_filter", []),
            "typing-extensions": ("4.15.0", "typing_extensions", []),
        }
        responses = {}
        for name, (version, wheel_name, requirements) in projects.items():
            wheel = distribution_file(
                f"{wheel_name}-{version}-py3-none-any.whl",
            )
            responses[f"https://example.invalid/simple/{name}/"] = (
                httpx.Response(200, json={
                    "versions": [version], "files": [wheel],
                })
            )
            fields = ["Metadata-Version: 2.1", f"Name: {name}"]
            fields += [f"Requires-Dist: {item}" for item in requirements]
            responses[wheel["url"] + ".metadata"] = httpx.Response(
                200, content=("\n".join(fields) + "\n\n").encode(),
            )
        http = Mock(spec=HttpClient)
        http.get.side_effect = lambda url, **kwargs: responses[url]
        builder = DependenciesTreeBuilder(DependenciesCollector(http))

        result = await builder("example.invalid/simple", "aiogram", "3.31.0")

        self.assertEqual(
            [node.package_name for node in result.dependencies],
            ["magic-filter", "typing-extensions"],
        )


if __name__ == "__main__":
    unittest.main()
