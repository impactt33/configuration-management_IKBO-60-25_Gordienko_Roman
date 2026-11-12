"""Точка входа CLI для построения графа зависимостей."""

import asyncio
import sys

import httpx

from hw2.core.arguments_parser import parse_command_line
from hw2.core.exceptions import AppError
from hw2.core.http_client import HttpClient
from hw2.main.data.external_api.dependencies_collector import (
    DependenciesCollector,
)
from hw2.main.data.file_dependencies_collector import FileDependenciesCollector
from hw2.main.domain.dependencies_repository import DependenciesRepository
from hw2.main.domain.dependencies_tree_builder import DependenciesTreeBuilder
from hw2.main.domain.entities.dependency_tree import Dependency
from hw2.main.domain.entities.exception_cause import ExceptionCause
from hw2.main.domain.entities.parameters import PackageManagerParameters
from hw2.main.output import emit_result


async def _build_tree(
    params: PackageManagerParameters, collector: DependenciesRepository,
) -> Dependency | ExceptionCause:
    """Передаёт одинаковые ограничения BFS обоим источникам данных."""
    builder = DependenciesTreeBuilder(collector)
    return await builder(
        params.repo_url, params.name, params.version,
        max_depth=params.max_depth, exclude_substring=params.filter,
    )


async def build_tree(
    params: PackageManagerParameters,
) -> Dependency | ExceptionCause:
    """Выбирает источник; HTTP-клиент создаётся только в сетевом режиме."""
    if params.test_mode:
        return await _build_tree(
            params, FileDependenciesCollector(params.repo_url),
        )
    http_client = HttpClient()
    try:
        return await _build_tree(params, DependenciesCollector(http_client))
    finally:
        http_client.close()


def main() -> int:
    """Печатает выбранный результат или ошибку без трассировки стека."""
    params = parse_command_line(PackageManagerParameters)
    try:
        result = asyncio.run(build_tree(params))
        if isinstance(result, ExceptionCause):
            print(
                f"Ошибка HTTP {result.status_code}: {result.cause}",
                file=sys.stderr,
            )
            return 1
        emit_result(result, params)
    except (
        AppError, httpx.HTTPError, httpx.InvalidURL, ValueError, OSError,
    ) as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
