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

    def __init__(self, vfs: VFS | None, logger: XmlLogger | None = None) -> None:
        """Начинает работу в корне загруженной VFS."""
        self.vfs = vfs
        self.logger = logger
        self.current_directory = vfs.root_directory if vfs is not None else None

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

        parts = pure_posix_path.parts[1:] if pure_posix_path.is_absolute() else pure_posix_path.parts
        for part in parts:
            if part == "..":
                if directory.parent is not None:
                    directory = directory.parent
                continue

            child_directory = next(
                (child for child in directory.directories if child.name == part),
                None,
            )
            if child_directory is None:
                if any(file.name == part for file in directory.files):
                    raise CommandError(f"{command}: {pure_posix_path}: not a directory.")
                raise CommandError(f"{command}: {pure_posix_path}: no such file or directory.")
            directory = child_directory

        return directory

    def cmd_ls(self, args: list[str]) -> str:
        """Заглушка ls: возвращает имя команды и аргументы."""

        if self.vfs is None or self.current_directory is None:
            raise CommandError("ls: VFS is not loaded.")

        answer = []
        list_flag = False

        if len(args) == 0:
            for directory in self.current_directory.directories:
                answer.append(directory.name)
            for file in self.current_directory.files:
                answer.append(file.name)
            return " ".join(answer)

        if args[0] == "-l":
            list_flag = True

        directory = self.go_to_directory("ls", args[1] if list_flag else args[0])

        for inner_directory in directory.directories:
            answer.append(inner_directory.name)
        for file in directory.files:
            answer.append(file.name)
        return " ".join(answer) if not list_flag else "\n".join(answer)

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
