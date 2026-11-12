"""Читает версии и требования из локального JSON-репозитория."""

import json
import re
from pathlib import Path

from packaging.requirements import InvalidRequirement, Requirement
from packaging.version import InvalidVersion, Version

from hw2.main.domain.exceptions import (
    PackageNotFoundError,
    RepositoryFileError,
    VersionNotFoundError,
)


class FileDependenciesCollector:
    """Использует формат {имя: {версия: [требования]}} без сети."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.packages = self._read_packages()

    def get_pypi_dependencies_for_package(
        self, host: str, name: str, version: str,
    ) -> list[str]:
        """Возвращает требования релиза, учитывая эквивалентные версии."""
        releases = self._get_releases(name)
        for release, requirements in releases.items():
            if Version(release) == Version(version):
                return list(requirements)
        raise VersionNotFoundError(
            f"В файле {self.path} нет версии {name}=={version}"
        )

    def get_available_versions_of_package(
        self, host: str, package_name: str,
    ) -> list[str]:
        """Возвращает версии только из загруженного файла."""
        return list(self._get_releases(package_name))

    def _get_releases(self, name: str) -> dict[str, list[str]]:
        """Выдаёт понятную ошибку при ссылке на отсутствующий пакет."""
        if name not in self.packages:
            raise PackageNotFoundError(
                f"В файле {self.path} нет пакета {name!r}"
            )
        return self.packages[name]

    def _read_packages(self) -> dict[str, dict[str, list[str]]]:
        """Загружает JSON и проверяет структуру до начала обхода."""
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise RepositoryFileError(
                f"Не удалось прочитать репозиторий {self.path}: {error}"
            ) from error
        if not isinstance(data, dict) or not data:
            raise RepositoryFileError(
                "Репозиторий должен быть непустым JSON-объектом"
            )
        for name, releases in data.items():
            self._validate_name(name)
            self._validate_releases(name, releases)
        return data

    @staticmethod
    def _validate_name(name: str) -> None:
        """Разрешает имена из больших латинских букв, как в задании."""
        if re.fullmatch(r"[A-Z]+", name) is None:
            raise RepositoryFileError(
                f"Имя пакета {name!r} должно состоять из букв A–Z"
            )

    @classmethod
    def _validate_releases(cls, name: str, releases: object) -> None:
        """Проверяет версии и списки требований каждого пакета."""
        if not isinstance(releases, dict) or not releases:
            raise RepositoryFileError(
                f"Для {name} нужен непустой объект версий"
            )
        seen = set()
        for version, requirements in releases.items():
            try:
                parsed = Version(version)
            except InvalidVersion as error:
                raise RepositoryFileError(
                    f"Некорректная версия {name}=={version}"
                ) from error
            if parsed in seen:
                raise RepositoryFileError(
                    f"У {name} дублируется версия {version}"
                )
            seen.add(parsed)
            if not isinstance(requirements, list):
                raise RepositoryFileError(
                    f"Зависимости {name}=={version} должны быть списком"
                )
            for requirement in requirements:
                cls._validate_requirement(requirement)

    @classmethod
    def _validate_requirement(cls, value: object) -> None:
        """Проверяет требования; прямые URL в файловом режиме запрещены."""
        if not isinstance(value, str):
            raise RepositoryFileError("Зависимость должна быть строкой")
        try:
            requirement = Requirement(value)
        except InvalidRequirement as error:
            raise RepositoryFileError(
                f"Некорректная зависимость {value!r}"
            ) from error
        cls._validate_name(requirement.name)
        if requirement.url is not None:
            raise RepositoryFileError(
                f"В тестовом репозитории нельзя использовать URL: {value}"
            )
