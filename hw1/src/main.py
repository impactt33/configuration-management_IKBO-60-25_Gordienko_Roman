"""Точка входа: разбирает параметры и запускает окно эмулятора."""

import argparse
import xml.etree.ElementTree as ET

from errors import InvalidVfs, VfsNotFound
from gui import ShellWindow
from logger import XmlLogger
from vfs_reader import get_vfs


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Разбирает параметры командной строки.

    Если argv не передан, берутся аргументы запуска программы.
    """
    parser = argparse.ArgumentParser(description="Эмулятор командной оболочки.")
    parser.add_argument("--vfs", metavar="PATH", help="Путь к файлу vfs.")
    parser.add_argument("--log", metavar="PATH", help="Путь к лог-файлу.")
    parser.add_argument(
        "--script", metavar="PATH", help="Путь к стартовому скрипту."
    )
    return parser.parse_args(argv)


def main() -> None:
    """Создаёт окно эмулятора и запускает его."""
    args = parse_args()

    vfs = None
    vfs_error = None
    try:
        vfs = get_vfs(args.vfs) if args.vfs else None
    except (VfsNotFound, InvalidVfs, OSError, ET.ParseError) as exc:
        vfs_error = f"VFS error: cannot load {args.vfs}: {exc}"

    logger = None
    log_error = None
    if args.log:
        try:
            logger = XmlLogger(args.log)
        except (OSError, ET.ParseError) as exc:
            log_error = f"Log error: cannot use {args.log}: {exc}"
    shell_window = ShellWindow(vfs, logger)
    for name, value in vars(args).items():
        shell_window.write(f"{name}: {value}")
    if log_error:
        shell_window.write(log_error)
    if vfs_error:
        shell_window.write(vfs_error)

    if args.script:
        shell_window.run_script(args.script)

    shell_window.run()


if __name__ == "__main__":
    main()
