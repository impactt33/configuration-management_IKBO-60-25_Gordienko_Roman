"""Проверки этапов 4–5 через CLI, включая настоящий D2 при его наличии."""

import os
from pathlib import Path
from shutil import which
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from xml.etree import ElementTree


HW2 = Path(__file__).resolve().parents[1]
D2_AVAILABLE = (HW2 / ".tools" / "d2").is_file() or which("d2")


class TestStage45CLI(unittest.TestCase):
    """Не использует сеть и не открывает настоящий браузер при проверках."""

    def setUp(self):
        """Создаёт выходной каталог только внутри hw2."""
        directory = TemporaryDirectory(dir=HW2 / "tests")
        self.addCleanup(directory.cleanup)
        self.output = Path(directory.name)

    def run_cli(self, *args, repository="branching", env=None):
        """Вызывает тот же bash-скрипт, которым пользуется пользователь."""
        return subprocess.run(
            ["bash", str(HW2 / "run.sh"), "--test-mode", "--repo",
             str(HW2 / "examples" / f"{repository}.json"), "--name", "A",
             "--version", "1.0", "--max-depth", "10", *args],
            cwd=HW2.parent, capture_output=True, text=True, timeout=15,
            env=dict(os.environ, PYTHON=sys.executable, **(env or {})),
        )

    def test_load_order_includes_root_last_and_respects_filter(self):
        """Режим порядка использует ограничения того же BFS."""
        result = self.run_cli("--format", "order", "--filter", "b")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            result.stdout.splitlines(), ["E==1.0", "C==1.0", "A==1.0"],
        )

    def test_load_order_cycle_has_error_and_no_partial_order(self):
        """Частичный результат не выдаётся как корректный порядок."""
        result = self.run_cli("--format", "order", repository="cycle")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")
        self.assertIn("цикл", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_d2_is_written_without_requiring_renderer(self):
        """Для текстового D2 внешний бинарник не нужен."""
        path = self.output / "graph with spaces.d2"
        result = self.run_cli(
            "--format", "d2", "--output", str(path),
            env={"D2_BINARY": "/missing/d2"},
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(path.read_text(), result.stdout)
        self.assertIn("n0 -> n1", result.stdout)

    @unittest.skipUnless(D2_AVAILABLE, "D2 не установлен")
    def test_svg_is_rendered_from_real_d2_including_cycle(self):
        """Настоящий D2 компилирует цикл в корректный SVG-документ."""
        path = self.output / "cycle with spaces.svg"
        result = self.run_cli(
            "--format", "d2", "--output", str(path), repository="cycle",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(path.with_suffix(".d2").read_text(), result.stdout)
        svg = ElementTree.parse(path).getroot()
        self.assertEqual(svg.tag, "{http://www.w3.org/2000/svg}svg")
        self.assertIn("A==1.0", path.read_text())

    def test_missing_renderer_is_an_error_without_traceback(self):
        """Отсутствующий D2 не маскируется сохранением одного текста."""
        result = self.run_cli(
            "--format", "d2", "--output", str(self.output / "graph.svg"),
            env={"D2_BINARY": "/missing/d2"},
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("D2", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_invalid_output_options_are_rejected_before_analysis(self):
        """Нельзя открывать не-SVG или перезаписывать входной репозиторий."""
        for options in (
            ["--show"], ["--format", "unknown"],
            ["--output", str(self.output / "graph.svg")],
            ["--output", str(HW2 / "examples" / "branching.json")],
        ):
            with self.subTest(options=options):
                result = self.run_cli(*options)
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertNotIn("Traceback", result.stderr)

    def test_stage4_demonstration_script(self):
        """Примеры включают ветвление, общий узел, лист и цикл."""
        result = subprocess.run(
            ["bash", str(HW2 / "examples" / "run_stage4.sh")],
            env=dict(os.environ, PYTHON=sys.executable),
            capture_output=True, text=True, timeout=15,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("цикл", result.stderr)
        self.assertIn("D==1.0", result.stdout)


if __name__ == "__main__":
    unittest.main()
