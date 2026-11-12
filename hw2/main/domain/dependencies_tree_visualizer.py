"""Преобразует граф зависимостей в текст диаграммы D2."""

import json

from hw2.main.domain.entities.dependency_tree import Dependency


class DependenciesTreeVisualizer:
    """Сохраняет узлы, общие зависимости и циклы в направленной диаграмме."""

    def __call__(self, root: Dependency) -> str:
        """Использует безопасные идентификаторы и экранирует подписи узлов."""
        graph = root.as_adjacency_list()
        identifiers = {name: f"n{index}" for index, name in enumerate(graph)}
        lines = ["direction: right", ""]
        for name, identifier in identifiers.items():
            label = json.dumps(name, ensure_ascii=False)
            lines.append(f"{identifier}: {label}")
        lines.extend(["", 'n0.style.fill: "#dbeafe"', ""])
        for parent, children in graph.items():
            for child in children:
                lines.append(f"{identifiers[parent]} -> {identifiers[child]}")
        return "\n".join(lines) + "\n"
