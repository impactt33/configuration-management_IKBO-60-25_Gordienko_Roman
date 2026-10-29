"""Исключения эмулятора оболочки."""


class ShellError(Exception):
    """Ошибка работы шелла, о которой нужно сообщить пользователю."""


class ParseError(ShellError):
    """Ошибка парсера: невалидная строка."""


class UnclosedQuote(ParseError):
    """В команде незакрытая кавычка."""

    def __init__(self, quote: str) -> None:
        """Формирует сообщение с незакрытой кавычкой."""
        super().__init__(f"Unclosed quote: {quote}")


class CommandError(ShellError):
    """Ошибка выполнения команды."""


class TooManyArguments(CommandError):
    """Команде передано слишком много аргументов."""

    def __init__(self, command: str) -> None:
        """Формирует сообщение с именем команды."""
        super().__init__(f"{command}: too many arguments.")


class UnknownCommand(CommandError):
    """Неизвестная команда."""

    def __init__(self, command: str) -> None:
        """Формирует сообщение с именем команды."""
        super().__init__(f"{command}: unknown command.")


class ExitRequest(Exception):
    """Просьба завершить приложение. Это не ошибка."""


class VfsNotFound(ParseError):
    """VFS по указанному пути не найдена."""

    def __init__(self, vfs_path: str) -> None:
        """Формирует сообщение с путём к VFS."""
        super().__init__(f"vfs by path {vfs_path} not found.")


class InvalidVfs(ParseError):
    """Невалидная VFS - отсутствует корневая папка."""

    def __init__(self, vfs_path: str) -> None:
        """Формирует сообщение с путём к VFS."""
        super().__init__(f"vfs by path {vfs_path} invalid.")
