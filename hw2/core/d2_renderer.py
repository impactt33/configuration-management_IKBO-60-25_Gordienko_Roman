"""Вызывает внешний D2 только для рендеринга готового описания графа."""

import os
from pathlib import Path
from shutil import which
import subprocess
from tempfile import TemporaryDirectory
import webbrowser

from hw2.main.domain.exceptions import VisualizationError


class D2Renderer:
    """Сохраняет исходный D2 рядом с SVG и проверяет ошибки компилятора."""

    def __init__(self, executable: str | None = None) -> None:
        local = Path(__file__).resolve().parents[1] / ".tools" / "d2"
        self.executable = (
            executable or os.environ.get("D2_BINARY") or which("d2")
            or (str(local) if local.is_file() else None)
        )

    def render(self, source: str, output: Path) -> Path:
        """Компилирует D2 в SVG без shell и с ограничением времени."""
        if self.executable is None:
            raise VisualizationError(
                "Не найден d2. Запустите hw2/tools/install_d2.py "
                "или укажите путь в D2_BINARY"
            )
        if output.suffix.lower() != ".svg":
            raise VisualizationError("Изображение должно иметь расширение .svg")
        output.parent.mkdir(parents=True, exist_ok=True)
        source_path = output.with_suffix(".d2")
        source_path.write_text(source, encoding="utf-8")
        with TemporaryDirectory(dir=output.parent, prefix=".d2-") as folder:
            rendered = Path(folder) / "graph.svg"
            self._compile(source_path, rendered)
            rendered.replace(output)
        return output

    def _compile(self, source: Path, output: Path) -> None:
        """Заменяет прошлый SVG только после успешного рендеринга нового."""
        try:
            result = subprocess.run(
                [self.executable, "--layout=dagre", "--theme=0",
                 str(source.resolve()), str(output.resolve())],
                capture_output=True, text=True, timeout=30,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            raise VisualizationError(f"Не удалось запустить D2: {error}") \
                from error
        if result.returncode != 0 or not output.is_file():
            raise VisualizationError(
                "Ошибка D2: " + (result.stderr.strip() or "SVG не создан")
            )

    @staticmethod
    def show(output: Path) -> None:
        """Передаёт SVG стандартному браузеру только по опции --show."""
        try:
            opened = webbrowser.open(output.resolve().as_uri())
        except webbrowser.Error as error:
            raise VisualizationError(f"Не удалось открыть SVG: {error}") \
                from error
        if not opened:
            raise VisualizationError(f"Откройте изображение вручную: {output}")
