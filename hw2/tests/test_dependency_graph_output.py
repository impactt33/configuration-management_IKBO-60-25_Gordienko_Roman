"""Проверки вывода графа без рекурсивного обхода моделей."""

import unittest

from hw2.main.domain.entities.dependency_tree import Dependency


class TestDependencyGraphOutput(unittest.TestCase):
    """Проверяет обратные рёбра, объединение веток и глубокие цепочки."""

    def test_equivalent_versions_share_one_vertex_in_cycle(self):
        """A==1.0 и A==1.0.0 обозначают одну вершину цикла."""
        back = Dependency(package_name="a", version="1.0.0", dependencies=[])
        child = Dependency(package_name="B", version="1.0", dependencies=[back])
        root = Dependency(package_name="A", version="1.0", dependencies=[child])

        self.assertEqual(root.as_adjacency_list(), {
            "A==1.0": ["B==1.0"], "B==1.0": ["A==1.0"],
        })

    def test_edges_of_repeated_vertices_are_merged(self):
        """Лист повторной ветки не стирает уже известные рёбра."""
        leaf = Dependency(package_name="D", version="1", dependencies=[])
        first = Dependency(package_name="B", version="1", dependencies=[leaf])
        second = Dependency(package_name="B", version="1", dependencies=[])
        root = Dependency(
            package_name="A", version="1", dependencies=[first, second],
        )

        self.assertEqual(root.as_adjacency_list(), {
            "A==1": ["B==1"], "B==1": ["D==1"], "D==1": [],
        })

    def test_deep_graph_output_does_not_use_pydantic_recursion(self):
        """Цепочка из 1101 узла выводится без model_dump и рекурсии."""
        root = Dependency(package_name="P0", version="1", dependencies=[])
        node = root
        for index in range(1, 1101):
            child = Dependency(
                package_name=f"P{index}", version="1", dependencies=[],
            )
            node.dependencies.append(child)
            node = child

        graph = root.as_adjacency_list()

        self.assertEqual(len(graph), 1101)
        self.assertEqual(graph["P1099==1"], ["P1100==1"])
        self.assertEqual(graph["P1100==1"], [])


if __name__ == "__main__":
    unittest.main()
