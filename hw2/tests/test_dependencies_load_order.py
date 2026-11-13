"""Проверки порядка загрузки и обработки циклов."""

import unittest

from hw2.main.domain.dependencies_load_order import DependenciesLoadOrder
from hw2.main.domain.entities.dependency_tree import Dependency
from hw2.main.domain.exceptions import CyclicDependencyError


def node(name, *children):
    """Создаёт маленький граф с версией 1.0 у каждого пакета."""
    return Dependency(
        package_name=name, version="1.0", dependencies=list(children),
    )


class TestDependenciesLoadOrder(unittest.TestCase):
    """Каждая зависимость должна идти до использующего её пакета."""

    def prepare_sorter(self):
        """Использует настоящий алгоритм без подмены результатов."""
        self.sort = DependenciesLoadOrder()

    def test_chain_and_leaf(self):
        """Цепочка идёт от листа к корню; одиночный пакет остаётся один."""
        self.prepare_sorter()
        self.assertEqual(
            self.sort(node("A", node("B", node("C")))),
            ["C==1.0", "B==1.0", "A==1.0"],
        )
        self.assertEqual(self.sort(node("A")), ["A==1.0"])

    def test_shared_dependency_occurs_once(self):
        """Общая зависимость загружается до обоих родителей ровно один раз."""
        self.prepare_sorter()
        root = node("A", node("C", node("D")), node("B", node("D")))
        self.assertEqual(
            self.sort(root), ["D==1.0", "B==1.0", "C==1.0", "A==1.0"],
        )

    def test_ties_do_not_depend_on_input_order(self):
        """Независимые вершины выбираются по имени для повторяемости."""
        self.prepare_sorter()
        self.assertEqual(
            self.sort(node("A", node("C"), node("B"))),
            self.sort(node("A", node("B"), node("C"))),
        )

    def test_cycle_and_self_loop_have_explicit_error(self):
        """Повторный конечный узел всё равно сохраняет цикл в графе."""
        self.prepare_sorter()
        for root in (node("A", node("B", node("A"))), node("A", node("A"))):
            with self.subTest(root=root.package_name):
                with self.assertRaisesRegex(CyclicDependencyError, "цикл"):
                    self.sort(root)

    def test_deep_order_does_not_use_recursion(self):
        """Порядок цепочки длиннее лимита рекурсии строится итеративно."""
        self.prepare_sorter()
        root = current = node("P0")
        for index in range(1, 1101):
            child = node(f"P{index}")
            current.dependencies.append(child)
            current = child
        order = self.sort(root)
        self.assertEqual(len(order), 1101)
        self.assertEqual(order[0], "P1100==1.0")
        self.assertEqual(order[-1], "P0==1.0")


if __name__ == "__main__":
    unittest.main()
