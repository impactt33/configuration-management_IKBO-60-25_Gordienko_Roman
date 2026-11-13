"""Проверки D2-экспорта и ошибок рендеринга."""

import json
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from hw2.core.d2_renderer import D2Renderer
from hw2.main.domain.dependencies_tree_visualizer import (
    DependenciesTreeVisualizer,
)
from hw2.main.domain.entities.dependency_tree import Dependency
from hw2.main.domain.exceptions import VisualizationError


def node(name, *children):
    """Создаёт узел без зависимости от CLI и репозитория."""
    return Dependency(
        package_name=name, version="1.0", dependencies=list(children),
    )


class TestDependenciesTreeVisualizer(unittest.TestCase):
    """Диаграмма должна сохранять все вершины и рёбра ровно один раз."""

    def test_cycle_shared_node_and_isolated_node(self):
        """Повторное имя не создаёт лишнюю вершину, цикл остаётся ребром."""
        root = node("A", node("B", node("D")), node("C", node("D")), node("A"))
        source = DependenciesTreeVisualizer()(root)
        self.assertEqual(source.count('"D==1.0"'), 1)
        self.assertIn("n1 -> n3", source)
        self.assertIn("n2 -> n3", source)
        self.assertIn("n0 -> n0", source)
        self.assertIn('n0: "A==1.0"', DependenciesTreeVisualizer()(node("A")))

    def test_labels_are_escaped_and_ids_do_not_contain_package_names(self):
        """Кавычки и специальные символы не превращаются в код D2."""
        name = 'my.package-"label"\\value'
        source = DependenciesTreeVisualizer()(node(name))
        self.assertIn(f"n0: {json.dumps(name + '==1.0')}", source)
        self.assertTrue(source.startswith("direction: right\n"))


class TestD2Renderer(unittest.TestCase):
    """Сбой внешнего инструмента не должен выглядеть как успешный рендер."""

    def prepare_renderer(self):
        """Хранит все временные артефакты внутри hw2/tests."""
        directory = TemporaryDirectory(dir=Path(__file__).parent)
        self.addCleanup(directory.cleanup)
        self.output = Path(directory.name) / "graph.svg"
        self.renderer = D2Renderer(executable="d2")

    def test_source_is_saved_and_renderer_receives_paths_without_shell(self):
        """Путь с пробелами остаётся одним аргументом процесса."""
        self.prepare_renderer()

        def render(command, **kwargs):
            Path(command[-1]).write_text("<svg/>", encoding="utf-8")
            self.assertNotIn("shell", kwargs)
            return subprocess.CompletedProcess(command, 0, "", "")

        with patch("hw2.core.d2_renderer.subprocess.run", side_effect=render):
            self.renderer.render("a -> b\n", self.output)
        self.assertEqual(self.output.read_text(), "<svg/>")
        self.assertEqual(self.output.with_suffix(".d2").read_text(), "a -> b\n")

    def test_nonzero_exit_timeout_and_missing_output_are_errors(self):
        """Неуспешные запуски дают доменную ошибку визуализации."""
        self.prepare_renderer()
        cases = [
            subprocess.CompletedProcess([], 1, "", "bad syntax"),
            subprocess.CompletedProcess([], 0, "", ""),
            subprocess.TimeoutExpired("d2", 30), FileNotFoundError("d2"),
        ]
        for result in cases:
            options = {"side_effect": result} if isinstance(result, Exception) \
                else {"return_value": result}
            with self.subTest(result=result):
                with patch("hw2.core.d2_renderer.subprocess.run", **options):
                    with self.assertRaises(VisualizationError):
                        self.renderer.render("a -> b\n", self.output)

    def test_show_uses_local_file_uri(self):
        """Открытие изображения требует явного вызова show."""
        self.prepare_renderer()
        browser = "hw2.core.d2_renderer.webbrowser.open"
        with patch(browser, return_value=True) as op:
            self.renderer.show(self.output)
        op.assert_called_once_with(self.output.resolve().as_uri())

    def test_previous_svg_is_preserved_when_new_output_is_missing(self):
        """Старый SVG не выдаётся за результат неудачной компиляции."""
        self.prepare_renderer()
        self.output.write_text("old SVG", encoding="utf-8")
        completed = subprocess.CompletedProcess([], 0, "", "")
        with patch("hw2.core.d2_renderer.subprocess.run",
                   return_value=completed):
            with self.assertRaises(VisualizationError):
                self.renderer.render("a -> b\n", self.output)
        self.assertEqual(self.output.read_text(), "old SVG")


if __name__ == "__main__":
    unittest.main()
