"""Порядок загрузки: зависимости раньше использующих их пакетов."""

from collections import defaultdict
from heapq import heapify, heappop, heappush

from hw2.main.domain.entities.dependency_tree import Dependency
from hw2.main.domain.exceptions import CyclicDependencyError


class DependenciesLoadOrder:
    """Выполняет итеративную топологическую сортировку алгоритмом Кана."""

    def __call__(self, root: Dependency) -> list[str]:
        """Возвращает каждый пакет один раз; циклы отклоняются явно."""
        graph = root.as_adjacency_list()
        remaining = {name: len(children) for name, children in graph.items()}
        dependents = self._build_dependents(graph)
        ready = [name for name, count in remaining.items() if count == 0]
        heapify(ready)
        order = []
        while ready:
            name = heappop(ready)
            order.append(name)
            for parent in dependents[name]:
                remaining[parent] -= 1
                if remaining[parent] == 0:
                    heappush(ready, parent)
        if len(order) != len(graph):
            unresolved = sorted(name for name, count in remaining.items()
                                if count > 0)
            raise CyclicDependencyError(
                "Нельзя построить строгий порядок: обнаружен цикл. "
                "Не упорядочены: " + ", ".join(unresolved)
            )
        return order

    @staticmethod
    def _build_dependents(
        graph: dict[str, list[str]],
    ) -> dict[str, list[str]]:
        """Сопоставляет пакету всех родителей, ожидающих его загрузки."""
        dependents: dict[str, list[str]] = defaultdict(list)
        for parent, children in graph.items():
            for child in children:
                dependents[child].append(parent)
        return dependents
