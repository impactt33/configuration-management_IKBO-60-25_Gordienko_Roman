"""Разбор и выполнение команд эмулятора оболочки."""
from pathlib import PurePosixPath

from errors import (
    ClearRequest, CommandError, ExitRequest, MissingArguments, TooManyArguments,
    UnclosedQuote, UnknownCommand,
)
from logger import XmlLogger
from vfs_reader import VFS, Directory

QUOTES = "\"'"


def parse_command(command: str) -> list[str]:
    """Разбивает строку на имя команды и аргументы.

    Учитывает одинарные и двойные кавычки. Всё после # вне кавычек
    считается комментарием и отбрасывается.

    Raises:
        ParseError: если кавычка не закрыта.
    """
    command_with_args: list[str] = []
    current_argument: str = ""
    quote_state: str | None = None
    argument_started = False

    for symbol in command:
        if quote_state is not None:
            if symbol == quote_state:
                quote_state = None
            else:
                current_argument += symbol
        elif symbol == "#":
            break
        elif symbol.isspace():
            if argument_started:
                command_with_args.append(current_argument)
            current_argument = ""
            argument_started = False
        elif symbol in QUOTES:
            quote_state = symbol
            argument_started = True
        else:
            current_argument += symbol
            argument_started = True

    if quote_state is not None:
        raise UnclosedQuote(quote_state)

    if argument_started:
        command_with_args.append(current_argument)

    return command_with_args


class Shell:
    """Исполняет команды и хранит текущий каталог виртуальной системы."""

    def __init__(
        self, vfs: VFS | None, logger: XmlLogger | None = None,
    ) -> None:
        """Начинает работу в корне загруженной VFS."""
        self.vfs = vfs
        self.logger = logger
        self.current_directory = (
            vfs.root_directory if vfs is not None else None
        )

    @property
    def current_path(self) -> str:
        """Собирает абсолютный UNIX-путь по родительским каталогам."""
        parts = []
        directory = self.current_directory

        while directory is not None and directory.parent is not None:
            parts.append(directory.name)
            directory = directory.parent

        return "/" + "/".join(reversed(parts))

    def go_to_directory(self, command: str, path: str) -> Directory:
        """Находит каталог по пути внутри VFS."""
        if self.vfs is None or self.current_directory is None:
            raise CommandError(f"{command}: VFS is not loaded.")

        pure_posix_path = PurePosixPath(path)

        directory = (
            self.vfs.root_directory
            if pure_posix_path.is_absolute()
            else self.current_directory
        )

        parts = (
            pure_posix_path.parts[1:]
            if pure_posix_path.is_absolute()
            else pure_posix_path.parts
        )
        for part in parts:
            if part == "..":
                if directory.parent is not None:
                    directory = directory.parent
                continue

            directory = self._find_child_directory(
                directory, part, command, pure_posix_path,
            )

        return directory

    @staticmethod
    def _find_child_directory(
        directory: Directory, name: str, command: str, path: PurePosixPath,
    ) -> Directory:
        """Находит дочернюю папку или объясняет, почему путь недоступен."""
        child_directory = next(
            (child for child in directory.directories if child.name == name),
            None,
        )
        if child_directory is not None:
            return child_directory
        if any(file.name == name for file in directory.files):
            raise CommandError(f"{command}: {path}: not a directory.")
        raise CommandError(f"{command}: {path}: no such file or directory.")

    def cmd_ls(self, args: list[str]) -> str:
        """Выводит содержимое текущего или указанного каталога VFS."""
        if self.vfs is None or self.current_directory is None:
            raise CommandError("ls: VFS is not loaded.")

        long_format = "-l" in args
        paths = [arg for arg in args if arg != "-l"]
        if len(paths) > 1:
            raise TooManyArguments("ls")

        directory = (
            self.go_to_directory("ls", paths[0])
            if paths else self.current_directory
        )
        names = [child.name for child in directory.directories]
        names.extend(file.name for file in directory.files)
        return ("\n" if long_format else " ").join(names)

    def cmd_cd(self, args: list[str]) -> str:
        """Переходит по абсолютному или относительному пути внутри VFS."""
        if len(args) > 1:
            raise TooManyArguments("cd")

        if len(args) < 1:
            raise MissingArguments("cd")

        if not args[0]:
            raise CommandError("cd: empty path.")

        self.current_directory = self.go_to_directory("cd", args[0])
        return ""

    def cmd_pwd(self, args: list[str]) -> str:
        """Возвращает абсолютный путь к текущему каталогу."""
        if len(args) > 1:
            raise TooManyArguments("pwd")

        directory = self.current_directory
        parts = []

        while directory is not None and directory.parent is not None:
            parts.append(directory.name)
            directory = directory.parent

        return "/" + "/".join(reversed(parts))

    @staticmethod
    def cmd_clear(args: list[str]) -> str:
        """Просит GUI очистить поле вывода."""
        if args:
            raise TooManyArguments("clear")

        raise ClearRequest()

    @staticmethod
    def cmd_exit(args: list[str]) -> str:
        """Бросает исключение, которое будет обработано GUI."""
        if args:
            raise TooManyArguments("exit")

        raise ExitRequest()

    def execute(self, line: str) -> str:
        """Выполняет введённую строку и возвращает текст для вывода."""
        command_line = parse_command(line)

        if not command_line:
            return ""

        if self.logger is not None:
            self.logger.log(command_line[0], command_line[1:])

        command = command_line[0]

        match command:
            case "cd":
                return self.cmd_cd(command_line[1:])
            case "ls":
                return self.cmd_ls(command_line[1:])
            case "exit":
                return self.cmd_exit(command_line[1:])
            case "clear":
                return self.cmd_clear(command_line[1:])
            case "pwd":
                return self.cmd_pwd(command_line[1:])
            case _:
                raise UnknownCommand(command_line[0])
