"""Форматирует результат анализа и сохраняет выбранные артефакты."""

import json
from pathlib import Path

from hw2.core.d2_renderer import D2Renderer
from hw2.main.domain.dependencies_load_order import DependenciesLoadOrder
from hw2.main.domain.dependencies_tree_visualizer import (
    DependenciesTreeVisualizer,
)
from hw2.main.domain.entities.dependency_tree import Dependency
from hw2.main.domain.entities.parameters import PackageManagerParameters


def format_result(root: Dependency, output_format: str) -> str:
    """Выбирает список смежности, порядок загрузки или диаграмму D2."""
    if output_format == "order":
        return "\n".join(DependenciesLoadOrder()(root)) + "\n"
    if output_format == "d2":
        return DependenciesTreeVisualizer()(root)
    return json.dumps(root.as_adjacency_list(), ensure_ascii=False, indent=2)


def emit_result(root: Dependency, params: PackageManagerParameters) -> None:
    """Печатает текст и при необходимости сохраняет файл или открывает SVG."""
    content = format_result(root, params.output_format)
    if params.output:
        path = Path(params.output)
        if params.output_format == "d2" and path.suffix.lower() == ".svg":
            renderer = D2Renderer()
            renderer.render(content, path)
            if params.show:
                renderer.show(path)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
    print(content, end="" if content.endswith("\n") else "\n")
