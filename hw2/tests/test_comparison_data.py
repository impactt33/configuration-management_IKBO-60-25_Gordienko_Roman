"""Проверки сравнения графов независимо от сети и установленных пакетов."""

import unittest

from hw2.tools.comparison_data import compare, pipdeptree_graph


class TestComparisonData(unittest.TestCase):
    """Различает несовпадение графа и разные допустимые порядки."""

    def test_independent_nodes_can_have_different_valid_orders(self):
        """Перестановка независимых пакетов не является ошибкой сортировки."""
        graph = {"A==1.0": ["B==1", "C==1"], "B==1": [], "C==1": []}
        result = compare(graph, graph, ["B", "C", "A"], ["C", "B", "A"])
        self.assertFalse(result["identical_order"])
        self.assertTrue(result["own_order_is_topological"])
        self.assertTrue(result["pip_order_is_topological"])
        self.assertEqual(result["only_own_nodes"], [])
        self.assertEqual(result["only_pip_edges"], [])

    def test_graph_differences_and_invalid_order_are_detected(self):
        """Сравнение состава не подменяется проверкой числа вершин."""
        own = {"A==1": ["B==1"], "B==1": []}
        reference = {"A==1": ["B==2"], "B==2": []}
        result = compare(own, reference, ["A", "B"], ["B", "A"])
        self.assertEqual(result["only_own_nodes"], ["b==1"])
        self.assertEqual(result["only_pip_nodes"], ["b==2"])
        self.assertFalse(result["own_order_is_topological"])

    def test_pipdeptree_graph_excludes_unrelated_environment_packages(self):
        """Пакеты инструмента сравнения не попадают в граф корневого пакета."""
        data = [
            {"package": {"key": "a", "installed_version": "1.0"},
             "dependencies": [{"key": "b", "installed_version": "1.0"}]},
            {"package": {"key": "b", "installed_version": "1.0"},
             "dependencies": []},
            {"package": {"key": "unrelated", "installed_version": "1"},
             "dependencies": []},
        ]
        self.assertEqual(pipdeptree_graph(data, "A"), {
            "a==1": ["b==1"], "b==1": [],
        })


if __name__ == "__main__":
    unittest.main()
