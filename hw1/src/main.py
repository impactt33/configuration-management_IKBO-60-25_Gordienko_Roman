"""Точка входа: запускает окно эмулятора оболочки."""

from gui import ShellWindow

VFS_NAME = "myvfs"


def main() -> None:
    """Создаёт окно эмулятора и запускает его."""
    shell_window = ShellWindow(VFS_NAME)
    shell_window.run()


if __name__ == "__main__":
    main()
