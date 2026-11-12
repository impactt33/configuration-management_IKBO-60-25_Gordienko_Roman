"""Проверки третьего этапа через обычный bash-запуск приложения."""

import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest


HW2 = Path(__file__).resolve().parents[1]


class TestStage3CLI(unittest.TestCase):
    """Запускает реальные файлы примеров без доступа к сети."""

    def run_cli(self, *arguments, cwd=None):
        """Использует Python текущего набора тестов и ограничивает ожидание."""
        environment = dict(os.environ, PYTHON=sys.executable)
        return subprocess.run(
            ["bash", str(HW2 / "run.sh"), *arguments],
            cwd=cwd or HW2.parent, env=environment,
            capture_output=True, text=True, timeout=10,
        )

    def example(self, repository="branching", name="A", *arguments):
        """Возвращает проверенный результат запуска тестового репозитория."""
        result = self.run_cli(
            "--test-mode", "--repo", str(HW2 / "examples" / repository)
            + ".json", "--name", name, "--version", "1.0", *arguments,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        return json.loads(result.stdout)

    def test_help_works_from_hw2_directory(self):
        """run.sh больше не обращается к отсутствующему src/run.py."""
        result = self.run_cli("--help", cwd=HW2)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--max-depth", result.stdout)

    def test_demonstration_script_runs_all_examples(self):
        """Сценарий демонстрации вызывает обычный CLI во всех восьми случаях."""
        result = subprocess.run(
            ["bash", str(HW2 / "examples" / "run_stage3.sh")],
            cwd=HW2.parent, env=dict(os.environ, PYTHON=sys.executable),
            capture_output=True, text=True, timeout=10,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        self.assertEqual(result.stdout.count('"A==1.0":'), 6)
        self.assertIn('"S==1.0":', result.stdout)
        self.assertIn("Пакет без зависимостей", result.stdout)

    def test_branching_and_version_selection(self):
        """CLI передаёт выбранные параметры настоящему BFS."""
        graph = self.example("branching", "A", "--max-depth", "2")
        self.assertEqual(graph, {
            "A==1.0": ["B==1.5", "C==1.0"],
            "B==1.5": ["D==1.0"], "C==1.0": ["E==1.0"],
            "D==1.0": [], "E==1.0": [],
        })

    def test_depth_zero_and_one(self):
        """Граница глубины действует при запуске через shell."""
        self.assertEqual(
            self.example("branching", "A", "--max-depth", "0"),
            {"A==1.0": []},
        )
        self.assertEqual(
            self.example("branching", "A", "--max-depth", "1"),
            {"A==1.0": ["B==1.5", "C==1.0"],
             "B==1.5": [], "C==1.0": []},
        )

    def test_filter_removes_entire_unreachable_branch(self):
        """Исключённый B не приводит к анализу D."""
        graph = self.example("branching", "A", "--filter", "b")
        self.assertEqual(graph, {
            "A==1.0": ["C==1.0"], "C==1.0": ["E==1.0"],
            "E==1.0": [],
        })

    def test_cycles_keep_back_edges_and_terminate(self):
        """Цикл и петля завершаются до таймаута процесса."""
        self.assertEqual(
            self.example("cycle", "A", "--max-depth", "10"),
            {"A==1.0": ["B==1.0"], "B==1.0": ["C==1.0"],
             "C==1.0": ["A==1.0"]},
        )
        self.assertEqual(
            self.example("cycle", "S", "--max-depth", "10"),
            {"S==1.0": ["S==1.0"]},
        )

    def test_shared_dependencies_and_leaf(self):
        """Обе ссылки на D сохраняются; отдельный лист имеет пустой список."""
        graph = self.example("shared", "A", "--max-depth", "4")
        self.assertEqual(graph["A==1.0"], ["B==1.0", "D==1.0"])
        self.assertEqual(graph["C==1.0"], ["D==1.0"])
        self.assertEqual(graph["D==1.0"], ["E==1.0"])
        self.assertEqual(self.example("branching", "D"), {"D==1.0": []})

    def test_path_with_spaces_is_preserved(self):
        """Shell и парсер сохраняют пробелы внутри пути репозитория."""
        with TemporaryDirectory(dir=HW2 / "tests") as directory:
            path = Path(directory) / "repo with spaces.json"
            path.write_text('{"A": {"1.0": []}}', encoding="utf-8")
            result = self.run_cli(
                "--test-mode", "--repo", str(path),
                "--name", "A", "--version", "1.0",
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), {"A==1.0": []})

    def test_invalid_arguments_report_usage_without_traceback(self):
        """Некорректные параметры завершаются кодом ошибки CLI 2."""
        base = ["--name", "A", "--version", "1.0"]
        for extra in (
            ["--max-depth", "-1"], ["--max-depth", "abc"],
            ["--name", ""], ["--version", "bad"], ["--repo", ""],
        ):
            with self.subTest(extra=extra):
                result = self.run_cli(*base, *extra)
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertNotIn("Traceback", result.stderr)

    def test_repository_errors_report_failure_without_traceback(self):
        """Ошибки файла, пакета и версии выводятся через обычный CLI."""
        source = str(HW2 / "examples" / "branching.json")
        for name, version, repository in (
            ("A", "1.0", str(HW2 / "examples" / "missing.json")),
            ("Z", "1.0", source), ("A", "99.0", source),
        ):
            with self.subTest(name=name, version=version):
                result = self.run_cli(
                    "--test-mode", "--repo", repository,
                    "--name", name, "--version", version,
                )
                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
