"""Проверки BFS-построителя на искусственном репозитории."""

import asyncio
import threading
import unittest
from unittest.mock import Mock, call

from hw2.main.domain.dependencies_tree_builder import DependenciesTreeBuilder
from hw2.main.data.external_api.dependencies_collector import (
    DependenciesCollector,
)
from hw2.main.domain.entities.exception_cause import ExceptionCause
from hw2.main.domain.exceptions import VersionNotFoundError


class _ConcurrencyProbe:
    """Измеряет пересечение запросов двух одновременно работающих потоков."""

    def __init__(self, graph):
        self.graph = graph
        self.barrier = threading.Barrier(2)
        self.lock = threading.Lock()
        self.active = 0
        self.peak = 0

    def __call__(self, repo, name, version):
        """Синхронизирует пары запросов и фиксирует максимум активности."""
        if name == "root":
            return self.graph[(name, version)]
        with self.lock:
            self.active += 1
            self.peak = max(self.peak, self.active)
        try:
            self.barrier.wait(timeout=3)
            return self.graph[(name, version)]
        finally:
            with self.lock:
                self.active -= 1


class TestDependenciesTreeBuilder(unittest.IsolatedAsyncioTestCase):
    """Проверяет выбор версий, условия, циклы и передачу ошибок."""

    def setUp(self):
        """Подменяет сетевой сборщик строгими ответами из словарей."""
        self.repo = "example.invalid/simple"
        self.graph = {}
        self.versions = {}
        self.collector = Mock(spec=DependenciesCollector)
        self.collector.get_pypi_dependencies_for_package.side_effect = (
            lambda repo, name, version: self.graph[(name, version)]
        )
        self.collector.get_available_versions_of_package.side_effect = (
            lambda repo, name: self.versions[name]
        )
        self.builder = DependenciesTreeBuilder(self.collector)

    async def test_leaf(self):
        """Пакет без зависимостей не требует выбора дочерних версий."""
        self.graph[("root", "1.0")] = []

        result = await self.builder(self.repo, "root", "1.0")

        self.assertEqual(result.package_name, "root")
        self.assertEqual(result.version, "1.0")
        self.assertEqual(result.dependencies, [])
        self.collector.get_available_versions_of_package.assert_not_called()

    async def test_packages_are_loaded_in_breadth_first_order(self):
        """Следующий уровень запрашивается после всех родителей уровня."""
        self.graph = {
            ("a", "1.0"): ["b", "c"],
            ("b", "1.0"): ["d"],
            ("c", "1.0"): ["e"],
            ("d", "1.0"): [],
            ("e", "1.0"): [],
        }
        self.versions = {name: ["1.0"] for name in ("b", "c", "d", "e")}
        order = []

        def collect(repo, name, version):
            order.append(name)
            return self.graph[(name, version)]

        self.collector.get_pypi_dependencies_for_package.side_effect = collect

        result = await self.builder(self.repo, "a", "1.0")

        self.assertEqual(order[0], "a")
        self.assertEqual(set(order[1:3]), {"b", "c"})
        self.assertEqual(set(order[3:]), {"d", "e"})
        self.assertEqual(
            [node.package_name for node in result.dependencies], ["b", "c"],
        )

    async def test_level_requests_overlap_with_concurrency_limit(self):
        """Запросы уровня пересекаются и соблюдают заданный лимит."""
        self.graph = {("root", "1.0"): ["b", "c", "d", "e"]}
        self.graph.update({(name, "1.0"): [] for name in ("b", "c", "d", "e")})
        self.versions = {name: ["1.0"] for name in ("b", "c", "d", "e")}
        probe = _ConcurrencyProbe(self.graph)
        self.collector.get_pypi_dependencies_for_package.side_effect = probe
        builder = DependenciesTreeBuilder(self.collector, max_concurrency=2)

        result = await builder(self.repo, "root", "1.0")

        self.assertEqual(len(result.dependencies), 4)
        self.assertEqual(probe.peak, 2)
        self.assertEqual(probe.active, 0)

    async def test_deep_chain_does_not_require_recursion(self):
        """Обход цепочки длиннее лимита рекурсии остаётся итеративным."""
        length = 1100
        self.graph = {
            (f"pkg{i}", "1.0"): [f"pkg{i + 1}"] for i in range(length)
        }
        self.graph[(f"pkg{length}", "1.0")] = []
        self.versions = {
            f"pkg{i}": ["1.0"] for i in range(1, length + 1)
        }

        node = await self.builder(self.repo, "pkg0", "1.0")

        depth = 0
        while node.dependencies:
            self.assertEqual(len(node.dependencies), 1)
            node = node.dependencies[0]
            depth += 1
        self.assertEqual(depth, length)

    def test_concurrency_limit_must_be_positive(self):
        """Нулевой лимит отклоняется вместо зависания на семафоре."""
        with self.assertRaises(ValueError):
            DependenciesTreeBuilder(self.collector, max_concurrency=0)

    async def test_requirement_uses_child_name_and_matching_version(self):
        """Требование разбирается, а версии сравниваются численно."""
        self.graph[("root", "1.0")] = ["child>=2,<3"]
        self.graph[("child", "2.10")] = []
        self.versions["child"] = ["1.0", "2.9", "2.10", "3.0"]

        result = await self.builder(self.repo, "root", "1.0")

        self.assertEqual(result.dependencies[0].package_name, "child")
        self.assertEqual(result.dependencies[0].version, "2.10")
        self.assertEqual(
            self.collector.get_available_versions_of_package.call_args_list,
            [call(self.repo, "child")],
        )
        self.assertEqual(
            self.collector.get_pypi_dependencies_for_package.call_args_list,
            [
                call(self.repo, "root", "1.0"),
                call(self.repo, "child", "2.10"),
            ],
        )

    async def test_false_environment_marker_skips_all_child_requests(self):
        """Неприменимая зависимость исключается до запросов к сборщику."""
        self.graph[("root", "1.0")] = [
            'child; python_version < "0"',
        ]

        result = await self.builder(self.repo, "root", "1.0")

        self.assertEqual(result.dependencies, [])
        self.collector.get_available_versions_of_package.assert_not_called()

    async def test_unselected_extra_is_skipped(self):
        """Дополнительная возможность не включается автоматически."""
        self.graph[("root", "1.0")] = ['tls; extra == "security"']

        result = await self.builder(self.repo, "root", "1.0")

        self.assertEqual(result.dependencies, [])
        self.collector.get_available_versions_of_package.assert_not_called()

    async def test_child_extras_are_propagated(self):
        """Выбранные extras относятся к зависимостям дочернего пакета."""
        self.graph = {
            ("root", "1.0"): ["child[security]>=1"],
            ("child", "1.0"): [
                "base", 'tls; extra == "security"',
                'docs; extra == "docs"',
            ],
            ("base", "1.0"): [],
            ("tls", "1.0"): [],
        }
        self.versions = {name: ["1.0"] for name in ("child", "base", "tls")}

        result = await self.builder(self.repo, "root", "1.0")

        self.assertEqual(
            [node.package_name for node in result.dependencies[0].dependencies],
            ["base", "tls"],
        )

    async def test_cycle_keeps_back_edge_without_reloading_root(self):
        """Цикл сохраняется листом, включая эквивалентные версии 1.0 и 1.0.0."""
        self.graph = {
            ("a", "1.0"): ["b"],
            ("b", "1.0"): ["a"],
        }
        self.versions = {"a": ["1.0.0"], "b": ["1.0"]}

        result = await self.builder(self.repo, "a", "1.0")

        back_edge = result.dependencies[0].dependencies[0]
        self.assertEqual(back_edge.package_name, "a")
        self.assertEqual(back_edge.dependencies, [])
        self.assertEqual(
            self.collector.get_pypi_dependencies_for_package.call_count, 2,
        )
        result.model_dump_json()

    async def test_cycle_with_new_extra_loads_extra_dependencies(self):
        """Повторный пакет с новым extra не теряет дополнительные связи."""
        self.graph = {
            ("a", "1.0"): ["b", 'tls; extra == "security"'],
            ("b", "1.0"): ["a[security]"],
            ("tls", "1.0"): [],
        }
        self.versions = {name: ["1.0"] for name in ("a", "b", "tls")}

        result = await self.builder(self.repo, "a", "1.0")

        repeated_a = result.dependencies[0].dependencies[0]
        self.assertEqual(
            [node.package_name for node in repeated_a.dependencies],
            ["b", "tls"],
        )
        self.assertEqual(repeated_a.dependencies[0].dependencies, [])
        result.model_dump_json()

    async def test_shared_dependency_remains_in_both_branches(self):
        """Общая зависимость не исчезает из второй ветки дерева."""
        self.graph = {
            ("a", "1.0"): ["b", "c"],
            ("b", "1.0"): ["d"],
            ("c", "1.0"): ["d"],
            ("d", "1.0"): ["e"],
            ("e", "1.0"): [],
        }
        self.versions = {name: ["1.0"] for name in ("b", "c", "d", "e")}

        result = await self.builder(self.repo, "a", "1.0")

        self.assertEqual(
            [
                branch.dependencies[0].package_name
                for branch in result.dependencies
            ],
            ["d", "d"],
        )
        for branch in result.dependencies:
            self.assertEqual(
                branch.dependencies[0].dependencies[0].package_name, "e",
            )
        calls = self.collector.get_pypi_dependencies_for_package.call_args_list
        self.assertEqual(calls.count(call(self.repo, "d", "1.0")), 1)

    async def test_cached_dependency_is_expanded_on_deeper_level(self):
        """Повторная ветка раскрывается из кэша даже без новых запросов."""
        self.graph = {
            ("a", "1.0"): ["b", "d"],
            ("b", "1.0"): ["c"],
            ("c", "1.0"): ["d"],
            ("d", "1.0"): ["e"],
            ("e", "1.0"): [],
        }
        self.versions = {name: ["1.0"] for name in ("b", "c", "d", "e")}

        result = await self.builder(self.repo, "a", "1.0")

        direct_d = result.dependencies[1]
        nested_d = result.dependencies[0].dependencies[0].dependencies[0]
        self.assertIsNot(direct_d, nested_d)
        for node in (direct_d, nested_d):
            self.assertEqual(node.package_name, "d")
            self.assertEqual(node.version, "1.0")
            self.assertEqual(node.dependencies[0].package_name, "e")
        calls = self.collector.get_pypi_dependencies_for_package.call_args_list
        for name in ("d", "e"):
            self.assertEqual(calls.count(call(self.repo, name, "1.0")), 1)

    async def test_version_lookup_error_is_returned(self):
        """Ошибка репозитория сохраняется вместо ошибки разбора версии."""
        error = ExceptionCause(status_code=503, cause="Repository unavailable")
        self.graph[("root", "1.0")] = ["child"]
        self.versions["child"] = error

        result = await self.builder(self.repo, "root", "1.0")

        self.assertIs(result, error)
        self.assertEqual(
            self.collector.get_pypi_dependencies_for_package.call_count, 1,
        )

    async def test_child_metadata_error_is_returned(self):
        """Ошибка получения дочерних метаданных передаётся вызывающему коду."""
        error = ExceptionCause(status_code=404, cause="Metadata not found")
        self.graph = {
            ("root", "1.0"): ["child"],
            ("child", "1.0"): error,
        }
        self.versions["child"] = ["1.0"]

        result = await self.builder(self.repo, "root", "1.0")

        self.assertIs(result, error)

    async def test_level_finishes_before_propagating_an_exception(self):
        """Ошибка не оставляет соседний запрос работать после возврата."""
        self.graph = {
            ("root", "1.0"): ["b", "c"], ("c", "1.0"): [],
        }
        self.versions = {"b": ["1.0"], "c": ["1.0"]}
        started = threading.Event()
        finished = threading.Event()
        release = threading.Event()

        def collect(repo, name, version):
            if name == "b":
                self.assertTrue(started.wait(timeout=3))
                raise VersionNotFoundError("simulated package failure")
            if name == "c":
                started.set()
                self.assertTrue(release.wait(timeout=3))
                finished.set()
            return self.graph[(name, version)]

        self.collector.get_pypi_dependencies_for_package.side_effect = collect
        timer = asyncio.get_running_loop().call_later(0.05, release.set)
        try:
            with self.assertRaises(VersionNotFoundError):
                await self.builder(self.repo, "root", "1.0")
            self.assertTrue(finished.is_set())
        finally:
            release.set()
            timer.cancel()

    async def test_no_matching_version_raises_version_error(self):
        """Отсутствие подходящего релиза даёт ошибку с именем зависимости."""
        self.graph[("root", "1.0")] = ["child>=2,<3"]
        self.versions["child"] = ["1.0", "3.0"]

        with self.assertRaisesRegex(VersionNotFoundError, "child"):
            await self.builder(self.repo, "root", "1.0")

    async def test_separate_calls_do_not_share_traversal_state(self):
        """Один построитель допускает повторное построение того же дерева."""
        self.graph[("root", "1.0")] = ["child"]
        self.graph[("child", "1.0")] = []
        self.versions["child"] = ["1.0"]

        first = await self.builder(self.repo, "root", "1.0")
        second = await self.builder(self.repo, "root", "1.0")

        self.assertEqual(first.model_dump(), second.model_dump())
        self.assertEqual(second.dependencies[0].package_name, "child")

    async def test_zero_depth_does_not_query_repository(self):
        """При глубине 0 возвращается только корень, без запросов."""
        result = await self.builder(
            self.repo, "root", "1.0", max_depth=0,
        )

        self.assertEqual(result.as_adjacency_list(), {"root==1.0": []})
        self.collector.get_pypi_dependencies_for_package.assert_not_called()
        self.collector.get_available_versions_of_package.assert_not_called()

    async def test_boundary_packages_are_not_loaded(self):
        """Для граничного узла выбирается версия, но не его зависимости."""
        self.graph[("a", "1.0")] = ["b"]
        self.versions["b"] = ["1.0"]

        result = await self.builder(self.repo, "a", "1.0", max_depth=1)

        self.assertEqual(result.as_adjacency_list(), {
            "a==1.0": ["b==1.0"], "b==1.0": [],
        })
        requests = self.collector.get_pypi_dependencies_for_package
        requests.assert_called_once_with(self.repo, "a", "1.0")

    async def test_depth_limit_applies_to_cached_nodes_in_each_branch(self):
        """Кэш не раскрывает граничный узел глубже разрешённого уровня."""
        self.graph = {
            ("a", "1.0"): ["b", "d"],
            ("b", "1.0"): ["c"],
            ("c", "1.0"): ["d"],
            ("d", "1.0"): ["e"],
            ("e", "1.0"): [],
        }
        self.versions = {name: ["1.0"] for name in ("b", "c", "d", "e")}

        result = await self.builder(self.repo, "a", "1.0", max_depth=3)

        self.assertEqual(
            result.dependencies[1].dependencies[0].package_name, "e",
        )
        boundary_d = result.dependencies[0].dependencies[0].dependencies[0]
        self.assertEqual(boundary_d.package_name, "d")
        self.assertEqual(boundary_d.dependencies, [])
        self.assertEqual(result.as_adjacency_list()["d==1.0"], ["e==1.0"])

    async def test_negative_depth_is_rejected(self):
        """Ошибочная глубина не превращается в неограниченный обход."""
        with self.assertRaises(ValueError):
            await self.builder(self.repo, "a", "1.0", max_depth=-1)
        self.collector.get_pypi_dependencies_for_package.assert_not_called()

    async def test_filter_skips_version_and_metadata_requests(self):
        """Фильтр применяется до любых запросов исключённого пакета."""
        self.graph[("root", "1.0")] = ["Typing_Extensions>=4"]

        result = await self.builder(
            self.repo, "root", "1.0", exclude_substring="TYPING.",
        )

        self.assertEqual(result.dependencies, [])
        self.collector.get_available_versions_of_package.assert_not_called()

    async def test_shared_descendant_survives_filter_in_another_branch(self):
        """Исключение b не исключает d, доступный через c."""
        self.graph = {
            ("a", "1.0"): ["b", "c"],
            ("c", "1.0"): ["d"],
            ("d", "1.0"): [],
        }
        self.versions = {name: ["1.0"] for name in ("c", "d")}

        result = await self.builder(
            self.repo, "a", "1.0", exclude_substring="B",
        )

        self.assertEqual(result.as_adjacency_list(), {
            "a==1.0": ["c==1.0"],
            "c==1.0": ["d==1.0"], "d==1.0": [],
        })

    async def test_matching_root_is_not_analyzed(self):
        """Корень остаётся в выводе, но его совпадение останавливает анализ."""
        result = await self.builder(
            self.repo, "root", "1.0", exclude_substring="ROOT",
        )

        self.assertEqual(result.dependencies, [])
        self.collector.get_pypi_dependencies_for_package.assert_not_called()

    async def test_limits_and_filters_are_not_reused_between_calls(self):
        """Каждый запуск одного построителя использует свои ограничения."""
        self.graph = {("a", "1.0"): ["b"], ("b", "1.0"): []}
        self.versions = {"b": ["1.0"]}

        await self.builder(self.repo, "a", "1.0", exclude_substring="b")
        result = await self.builder(self.repo, "a", "1.0", max_depth=1)

        self.assertEqual(result.dependencies[0].package_name, "b")


if __name__ == "__main__":
    unittest.main()
