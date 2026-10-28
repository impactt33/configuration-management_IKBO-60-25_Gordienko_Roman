"""Графический интерфейс эмулятора оболочки на tkinter."""

import getpass
import socket
import tkinter as tk
from pathlib import Path

from errors import ExitRequest, ShellError
from logger import XmlLogger
from shell import execute

WINDOW_SIZE = "800x500"
FONT = ("monospace", 22)
BACKGROUND = "black"
FOREGROUND = "white"


class ShellWindow:
    """Окно эмулятора: поле вывода и строка ввода команд."""

    def __init__(self, vfs_name: str, logger: XmlLogger | None = None) -> None:
        """Создаёт окно, имя VFS показывается в заголовке.

        Если передан logger, выполненные команды записываются в лог.
        """
        self.root = tk.Tk()
        self.root.title(f"Shell emulator - VFS: {vfs_name}")
        self.root.geometry(WINDOW_SIZE)
        self.prompt = f"{getpass.getuser()}@{socket.gethostname()}:~$ "
        self.output = self._build_output()
        self.entry = self._build_input()
        self.logger = logger

    def _build_output(self) -> tk.Text:
        """Создаёт поле вывода с прокруткой, недоступное для ввода."""
        frame = tk.Frame(self.root)
        frame.pack(fill=tk.BOTH, expand=True)
        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        output = tk.Text(
            frame, font=FONT, bg=BACKGROUND, fg=FOREGROUND,
            state=tk.DISABLED, yscrollcommand=scrollbar.set,
        )
        output.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=output.yview)
        return output

    def _build_input(self) -> tk.Entry:
        """Создаёт строку ввода с приглашением и обработчиком Enter."""
        frame = tk.Frame(self.root, bg=BACKGROUND)
        frame.pack(fill=tk.X)
        label = tk.Label(
            frame, text=self.prompt, font=FONT,
            bg=BACKGROUND, fg=FOREGROUND,
        )
        label.pack(side=tk.LEFT)
        entry = tk.Entry(
            frame, font=FONT, bg=BACKGROUND, fg=FOREGROUND,
            insertbackground=FOREGROUND, relief=tk.FLAT,
        )
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        entry.bind("<Return>", self._on_enter)
        entry.focus_set()
        return entry

    def _on_enter(self, event: tk.Event) -> None:
        """Забирает строку из поля ввода и выполняет её."""
        line = self.entry.get()
        self.entry.delete(0, tk.END)
        self.run_line(line)

    def _run(self, line: str) -> None:
        """Печатает строку как ввод, выполняет её и печатает результат.

        Ошибки не перехватываются: их обрабатывает вызывающий метод.
        """
        self.write(self.prompt + line)
        result = execute(line, self.logger)
        if result:
            self.write(result)

    def run_line(self, line: str) -> None:
        """Выполняет строку так, будто её ввёл пользователь."""
        try:
            self._run(line)
        except ShellError as exc:
            self.write(str(exc))
        except ExitRequest:
            self.root.destroy()

    def run_script(self, script_path: str) -> None:
        """Выполняет стартовый скрипт построчно, как диалог с пользователем.

        Пустые строки пропускаются. На первой ошибке выполнение
        останавливается, команда exit закрывает окно.
        """
        try:
            lines = Path(script_path).read_text(encoding="utf-8").splitlines()
        except OSError:
            self.write(f"Script error: cannot read {script_path}")
            return

        for number, line in enumerate(lines, start=1):
            if not line.strip():
                continue
            try:
                self._run(line)
            except ShellError as exc:
                self.write(str(exc))
                self.write(f"Script error at line {number}, execution stopped.")
                return
            except ExitRequest:
                self.root.destroy()
                return

    def write(self, text: str) -> None:
        """Добавляет строку в поле вывода и прокручивает его вниз."""
        self.output.config(state=tk.NORMAL)
        self.output.insert(tk.END, text + "\n")
        self.output.config(state=tk.DISABLED)
        self.output.see(tk.END)

    def run(self) -> None:
        """Запускает цикл обработки событий окна."""
        self.root.mainloop()
