"""Общий интерфейс сетевого и файлового репозиториев."""

from typing import Protocol

from hw2.main.domain.entities.exception_cause import ExceptionCause


class DependenciesRepository(Protocol):
    """Предоставляет версии пакета и его прямые зависимости."""

    def get_pypi_dependencies_for_package(
        self, host: str, name: str, version: str,
    ) -> list[str] | ExceptionCause:
        """Возвращает требования выбранной версии пакета."""
        ...

    def get_available_versions_of_package(
        self, host: str, package_name: str,
    ) -> list[str] | ExceptionCause:
        """Возвращает опубликованные версии пакета."""
        ...
