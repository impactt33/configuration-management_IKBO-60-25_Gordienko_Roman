"""Отдельная демонстрация этапов 4–5; приложение не использует pipdeptree."""

import argparse
import asyncio
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import venv

from hw2.core.d2_renderer import D2Renderer
from hw2.main.domain.dependencies_load_order import DependenciesLoadOrder
from hw2.main.domain.dependencies_tree_visualizer import (
    DependenciesTreeVisualizer,
)
from hw2.main.domain.entities.exception_cause import ExceptionCause
from hw2.main.domain.entities.parameters import PackageManagerParameters
from hw2.run import build_tree
from hw2.tools.comparison_data import compare, pipdeptree_graph


HW2 = Path(__file__).resolve().parents[1]
DEFAULT_PACKAGES = ["httpx==0.28.1", "requests==2.32.3", "rich==13.9.4"]


def environment() -> dict[str, str]:
    """Направляет кеши, временные файлы и пользовательские записи в hw2."""
    cache = HW2 / ".cache"
    (cache / "tmp").mkdir(parents=True, exist_ok=True)
    return dict(
        os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONNOUSERSITE="1",
        PYTHONPATH=str(HW2.parent), PIP_CONFIG_FILE=os.devnull,
        PIP_CACHE_DIR=str(cache / "pip"), PIP_DISABLE_PIP_VERSION_CHECK="1",
        PIP_INDEX_URL="https://pypi.org/simple/", PIP_EXTRA_INDEX_URL="",
        TMPDIR=str(cache / "tmp"), XDG_CACHE_HOME=str(cache),
        NO_COLOR="1", PIP_PROGRESS_BAR="off",
    )


def run(command: list[str], env: dict[str, str]) -> str:
    """Ожидает внешний инструмент и сохраняет его диагностику при ошибке."""
    result = subprocess.run(
        command, env=env, capture_output=True, text=True, timeout=180,
    )
    if result.returncode:
        raise RuntimeError(
            f"{' '.join(command)}\n{result.stdout}\n{result.stderr}"
        )
    return result.stdout


def create_environment(path: Path) -> Path:
    """Создаёт отдельное окружение без установки pip в проектную .venv."""
    python = path / "bin" / "python"
    if not python.is_file():
        venv.EnvBuilder(with_pip=False).create(path)
    return python


def pip_install(python: Path, env: dict[str, str], arguments: list[str]) -> str:
    """Вызывает pip для отдельного интерпретатора, разрешая только wheels."""
    return run([
        sys.executable, "-B", "-m", "pip", "--python", str(python),
        "install", "--no-input", "--only-binary=:all:", "--no-compile",
        *arguments,
    ], env)


def prepare_reference_tool(env: dict[str, str]) -> Path:
    """Устанавливает pipdeptree и Graphviz-обёртку в изолированный каталог."""
    python = create_environment(HW2 / ".tools" / "reference")
    marker = python.parent.parent / ".ready-2.30.0"
    if not marker.exists():
        pip_install(python, env, ["pipdeptree[graphviz]==2.30.0"])
        marker.touch()
    return python


def save_json(path: Path, value: object) -> None:
    """Сохраняет данные сравнения с читаемым UTF-8 форматированием."""
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8")


def own_results(
    name: str, version: str, output: Path,
) -> tuple[dict, list[str]]:
    """Использует самостоятельный сборщик приложения, затем рендерит D2."""
    params = PackageManagerParameters(name=name, version=version, max_depth=100)
    tree = asyncio.run(build_tree(params))
    if isinstance(tree, ExceptionCause):
        raise RuntimeError(tree.cause)
    graph = tree.as_adjacency_list()
    order = DependenciesLoadOrder()(tree)
    save_json(output / "graph.json", graph)
    (output / "order.txt").write_text("\n".join(order) + "\n", encoding="utf-8")
    source = DependenciesTreeVisualizer()(tree)
    D2Renderer().render(source, output / "graph.svg")
    return graph, order


def reference_results(
    name: str, version: str, output: Path, tool: Path, env: dict[str, str],
) -> tuple[dict, list[str]]:
    """Фиксирует фактическую установку pip и независимый вывод pipdeptree."""
    python = create_environment(HW2 / ".cache" / "reference-envs" / name)
    log = pip_install(python, env, [
        "--ignore-installed", "--report", str(output / "pip-report.json"),
        f"{name}=={version}",
    ])
    (output / "pip-install.log").write_text(log, encoding="utf-8")
    order_line = next(line for line in log.splitlines()
                      if line.startswith("Installing collected packages:"))
    order = order_line.split(":", 1)[1].strip().split(", ")
    base = [str(tool), "-B", "-m", "pipdeptree", "--python", str(python),
            "--warn", "silence"]
    data = json.loads(run([*base, "--json"], env))
    save_json(output / "pipdeptree.json", data)
    svg = run([*base, "--packages", name, "--graph-output", "svg"], env)
    (output / "pipdeptree.svg").write_text(svg, encoding="utf-8")
    return pipdeptree_graph(data, name), order


def demonstrate(package: str, destination: Path, tool: Path, env: dict) -> dict:
    """Сохраняет два рисунка, оба порядка и различия для одного пакета."""
    name, version = package.split("==", 1)
    output = destination / name
    output.mkdir(parents=True, exist_ok=True)
    print(f"Получение графа {package}…", flush=True)
    own, order = own_results(name, version, output)
    reference, pip_order = reference_results(name, version, output, tool, env)
    result = compare(own, reference, order, pip_order)
    result.update(package=package, python=platform.python_version(),
                  timestamp=datetime.now(timezone.utc).isoformat())
    save_json(output / "comparison.json", result)
    print(f"{package}: {len(own)} узлов; результаты сохранены", flush=True)
    return result


def main() -> None:
    """Демонстрирует три пакета или явно переданный список --package."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", action="append")
    parser.add_argument("--output", type=Path,
                        default=HW2 / "examples" / "results")
    args = parser.parse_args()
    env = environment()
    print("Подготовка изолированного pipdeptree…", flush=True)
    tool = prepare_reference_tool(env)
    results = [demonstrate(package, args.output.resolve(), tool, env)
               for package in args.package or DEFAULT_PACKAGES]
    save_json(args.output / "summary.json", results)


if __name__ == "__main__":
    main()
