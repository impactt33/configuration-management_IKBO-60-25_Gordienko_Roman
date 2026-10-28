"""Графический интерфейс эмулятора оболочки на tkinter."""

import getpass
import socket
import tkinter as tk

from shell import ExitRequest, execute

WINDOW_SIZE = "800x500"
FONT = ("monospace", 11)
BACKGROUND = "black"
FOREGROUND = "white"


class ShellWindow:
    """Окно эмулятора: поле вывода и строка ввода команд."""

    def __init__(self, vfs_name: str) -> None:
        """Создаёт окно, имя VFS показывается в заголовке."""
        self.root = tk.Tk()
        self.root.title(f"Shell emulator - VFS: {vfs_name}")
        self.root.geometry(WINDOW_SIZE)
        self.prompt = f"{getpass.getuser()}@{socket.gethostname()}:~$ "
        self.output = self._build_output()
        self.entry = self._build_input()

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

    def run_line(self, line: str) -> None:
        """Выполняет строку так, будто её ввёл пользователь."""
        self.write(self.prompt + line)
        try:
            result = execute(line)
        except ExitRequest:
            self.root.destroy()
            return
        if result:
            self.write(result)

    def write(self, text: str) -> None:
        """Добавляет строку в поле вывода и прокручивает его вниз."""
        self.output.config(state=tk.NORMAL)
        self.output.insert(tk.END, text + "\n")
        self.output.config(state=tk.DISABLED)
        self.output.see(tk.END)

    def run(self) -> None:
        """Запускает цикл обработки событий окна."""
        self.root.mainloop()
