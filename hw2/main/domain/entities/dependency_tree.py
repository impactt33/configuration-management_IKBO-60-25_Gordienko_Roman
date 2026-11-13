"""Узел дерева и итеративное представление графа для вывода."""

from collections import deque

from packaging.utils import canonicalize_name
from packaging.version import Version
from pydantic import BaseModel


class Dependency(BaseModel):
    """Хранит пакет, выбранную версию и дочерние зависимости."""

    package_name: str
    version: str
    dependencies: list[Dependency]

    def as_adjacency_list(self) -> dict[str, list[str]]:
        """Сохраняет общие связи и циклы без рекурсивной сериализации."""
        graph: dict[str, list[str]] = {}
        labels: dict[tuple[str, Version], str] = {}
        queue = deque([self])
        visited = set()

        def label(node: Dependency) -> str:
            key = canonicalize_name(node.package_name), Version(node.version)
            return labels.setdefault(
                key, f"{node.package_name}=={node.version}",
            )

        while queue:
            node = queue.popleft()
            if id(node) in visited:
                continue
            visited.add(id(node))
            links = graph.setdefault(label(node), [])
            for child in node.dependencies:
                target = label(child)
                if target not in links:
                    links.append(target)
                queue.append(child)
        return graph
