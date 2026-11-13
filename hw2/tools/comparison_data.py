"""Сравнивает результаты приложения с данными эталонного инструмента."""

from packaging.utils import canonicalize_name, canonicalize_version


def normalize_label(label: str) -> str:
    """Устраняет различия регистра, разделителей и эквивалентных версий."""
    name, version = label.split("==", 1)
    return f"{canonicalize_name(name)}=={canonicalize_version(version)}"


def normalize_graph(graph: dict[str, list[str]]) -> dict[str, list[str]]:
    """Нормализует подписи без зависимости от расположения узлов на рисунке."""
    return {
        normalize_label(name): sorted({normalize_label(child)
                                      for child in children})
        for name, children in graph.items()
    }


def pipdeptree_graph(data: list[dict], root: str) -> dict[str, list[str]]:
    """Извлекает достижимые узлы из JSON pipdeptree только для сравнения."""
    packages = {
        canonicalize_name(item["package"]["key"]): item for item in data
    }
    graph = {}
    pending = [canonicalize_name(root)]
    visited = set()
    while pending:
        name = pending.pop()
        if name in visited:
            continue
        visited.add(name)
        item = packages[name]
        parent = f"{name}=={item['package']['installed_version']}"
        graph[parent] = [
            f"{child['key']}=={child['installed_version']}"
            for child in item["dependencies"]
        ]
        pending.extend(canonicalize_name(child["key"])
                       for child in item["dependencies"])
    return normalize_graph(graph)


def graph_edges(graph: dict[str, list[str]]) -> set[tuple[str, str]]:
    """Возвращает уникальные направленные рёбра графа."""
    return {(parent, child) for parent, children in graph.items()
            for child in children}


def valid_order(order: list[str], graph: dict[str, list[str]]) -> bool:
    """Проверяет множество пакетов и правило «зависимость раньше родителя»."""
    names = [canonicalize_name(label.split("==", 1)[0]) for label in graph]
    if len(order) != len(set(order)) or set(order) != set(names):
        return False
    positions = {name: index for index, name in enumerate(order)}
    return all(
        positions[child.split("==", 1)[0]] < positions[parent.split("==", 1)[0]]
        for parent, child in graph_edges(graph)
    )


def compare(
    own: dict[str, list[str]], reference: dict[str, list[str]],
    own_order: list[str], pip_order: list[str],
) -> dict:
    """Разделяет различия состава графа и допустимые различия порядка."""
    own = normalize_graph(own)
    reference = normalize_graph(reference)
    own_order = [canonicalize_name(item.split("==", 1)[0])
                 for item in own_order]
    pip_order = [canonicalize_name(item) for item in pip_order]
    return {
        "own_node_count": len(own), "pip_node_count": len(reference),
        "own_edge_count": len(graph_edges(own)),
        "pip_edge_count": len(graph_edges(reference)),
        "only_own_nodes": sorted(own.keys() - reference.keys()),
        "only_pip_nodes": sorted(reference.keys() - own.keys()),
        "only_own_edges": sorted(graph_edges(own) - graph_edges(reference)),
        "only_pip_edges": sorted(graph_edges(reference) - graph_edges(own)),
        "own_order": own_order, "pip_order": pip_order,
        "identical_order": own_order == pip_order,
        "own_order_is_topological": valid_order(own_order, own),
        "pip_order_is_topological": valid_order(pip_order, reference),
    }
