import asyncio
from collections import deque
from dataclasses import dataclass

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name
from packaging.version import Version

from hw2.main.domain.dependencies_repository import DependenciesRepository
from hw2.main.domain.entities.dependency_tree import Dependency
from hw2.main.domain.entities.exception_cause import ExceptionCause
from hw2.main.domain.exceptions import VersionNotFoundError


DependencyKey = tuple[str, Version, frozenset[str]]
ResolvedDependency = tuple[Requirement, str]


@dataclass(frozen=True)
class QueueItem:
    """Хранит пакет, его место в дереве и путь до него."""

    requirement: Requirement
    node: Dependency
    path: frozenset[DependencyKey] = frozenset()

    @property
    def key(self) -> DependencyKey:
        """Различает версии и extras с учётом нормализации имён."""
        return (
            canonicalize_name(self.requirement.name),
            Version(self.node.version),
            frozenset(
                canonicalize_name(extra)
                for extra in self.requirement.extras
            ),
        )


class DependenciesTreeBuilder:
    """Строит дерево обходом BFS с параллельной обработкой уровня."""

    def __init__(
        self, dependencies_collector: DependenciesRepository,
        max_concurrency: int = 5,
    ) -> None:
        if max_concurrency < 1:
            raise ValueError("max_concurrency must be positive")
        self.deps_collector = dependencies_collector
        self.max_concurrency = max_concurrency

    async def __call__(
        self, repo_url: str, package_name: str, version: str,
        *, max_depth: int | None = None, exclude_substring: str = "",
    ) -> Dependency | ExceptionCause:
        """Обходит уровни до max_depth; глубина корня равна нулю."""
        if max_depth is not None and max_depth < 0:
            raise ValueError("max_depth must be non-negative")
        requirement = Requirement(package_name)
        root = Dependency(
            package_name=requirement.name, version=version, dependencies=[],
        )
        if self._is_excluded(requirement.name, exclude_substring):
            return root
        queue = deque([QueueItem(requirement=requirement, node=root)])
        cache: dict[DependencyKey, list[ResolvedDependency]] = {}
        limit = asyncio.Semaphore(self.max_concurrency)
        depth = 0

        while queue and (max_depth is None or depth < max_depth):
            error = await self._expand_level(
                repo_url, queue, cache, limit, exclude_substring,
            )
            if error is not None:
                return error
            depth += 1

        return root

    async def _expand_level(
        self, repo_url: str, queue: deque[QueueItem],
        cache: dict[DependencyKey, list[ResolvedDependency]],
        limit: asyncio.Semaphore, exclude_substring: str,
    ) -> ExceptionCause | None:
        """Загружает текущий уровень и формирует очередь следующего."""
        level = [queue.popleft() for _ in range(len(queue))]
        pending = {
            item.key: item for item in level if item.key not in cache
        }
        if pending:
            loaded = await self._load_level(
                repo_url, pending, limit, exclude_substring,
            )
            if isinstance(loaded, ExceptionCause):
                return loaded
            cache.update(loaded)

        for item in level:
            self._enqueue_dependencies(item, cache[item.key], queue)
        return None

    async def _load_level(
        self, repo_url: str, pending: dict[DependencyKey, QueueItem],
        limit: asyncio.Semaphore, exclude_substring: str,
    ) -> dict[DependencyKey, list[ResolvedDependency]] | ExceptionCause:
        """Ожидает завершения всего уровня, включая задачи с ошибками."""
        results = await asyncio.gather(
            *(
                self._load_dependencies(
                    repo_url, item, limit, exclude_substring,
                )
                for item in pending.values()
            ),
            return_exceptions=True,
        )
        loaded = {}
        for key, result in zip(pending, results):
            if isinstance(result, BaseException):
                raise result
            if isinstance(result, ExceptionCause):
                return result
            loaded[key] = result
        return loaded

    async def _load_dependencies(
        self, repo_url: str, item: QueueItem, limit: asyncio.Semaphore,
        exclude_substring: str,
    ) -> list[ResolvedDependency] | ExceptionCause:
        """Получает прямые зависимости в пределах лимита параллелизма."""
        async with limit:
            dependency_names = await asyncio.to_thread(
                self.deps_collector.get_pypi_dependencies_for_package,
                repo_url, item.requirement.name, item.node.version,
            )
            if isinstance(dependency_names, ExceptionCause):
                return dependency_names

            dependencies = []
            for dependency_name in dependency_names:
                child = Requirement(dependency_name)
                if self._is_excluded(child.name, exclude_substring):
                    continue
                if not self._is_applicable(child, item.requirement.extras):
                    continue
                child_version = await self._parse_dependency_modifiers(
                    repo_url, dependency_name,
                )
                if isinstance(child_version, ExceptionCause):
                    return child_version
                dependencies.append((child, child_version))
            return dependencies

    @staticmethod
    def _enqueue_dependencies(
        item: QueueItem, dependencies: list[ResolvedDependency],
        queue: deque[QueueItem],
    ) -> None:
        """Сохраняет связи и ставит следующий уровень в очередь."""
        path = item.path | {item.key}
        for requirement, version in dependencies:
            node = Dependency(
                package_name=requirement.name, version=version,
                dependencies=[],
            )
            item.node.dependencies.append(node)
            child = QueueItem(
                requirement=requirement, node=node, path=path,
            )
            if child.key not in path:
                queue.append(child)

    @staticmethod
    def _is_excluded(package_name: str, substring: str) -> bool:
        """Сравнивает подстроку с нормализованным именем пакета."""
        return bool(substring) and (
            canonicalize_name(substring) in canonicalize_name(package_name)
        )

    @staticmethod
    def _is_applicable(requirement: Requirement, extras: set[str]) -> bool:
        """Проверяет marker для текущей среды и выбранных extras пакета."""
        if requirement.marker is None:
            return True
        return any(
            requirement.marker.evaluate({"extra": extra})
            for extra in extras or {""}
        )

    async def _parse_dependency_modifiers(
        self, repo_url: str, dependency_name: str,
    ) -> str | ExceptionCause:
        """Выбирает максимальную опубликованную версию по ограничениям."""

        dependency = Requirement(dependency_name)
        available_versions = await asyncio.to_thread(
            self.deps_collector.get_available_versions_of_package,
            repo_url, dependency.name,
        )
        if isinstance(available_versions, ExceptionCause):
            return available_versions

        max_available_version = max(
            dependency.specifier.filter(available_versions),
            key=Version,
            default=None,
        )

        if max_available_version is None:
            raise VersionNotFoundError(
                f"No version of {dependency.name!r} matches "
                f"{str(dependency.specifier)!r}"
            )

        return max_available_version
