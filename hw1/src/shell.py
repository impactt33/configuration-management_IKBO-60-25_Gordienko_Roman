"""Разбор и выполнение команд эмулятора оболочки."""

QUOTES = "\"'"


class ParseError(Exception):
    """Ошибка парсера: невалидная строка."""


class ExitRequest(Exception):
    """Просьба завершить приложение."""


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

    for symbol in command:
        if quote_state is not None:
            if symbol == quote_state:
                quote_state = None
            else:
                current_argument += symbol
        elif symbol == "#":
            break
        elif symbol.isspace():
            if current_argument:
                command_with_args.append(current_argument)
            current_argument = ""
        elif symbol in QUOTES:
            quote_state = symbol
        else:
            current_argument += symbol

    if quote_state is not None:
        raise ParseError(f"Unclosed quote: {quote_state}")

    if current_argument:
        command_with_args.append(current_argument)

    return command_with_args


def cmd_ls(args: list[str]) -> str:
    """Заглушка ls: возвращает имя команды и аргументы."""
    return f"ls: {args}"


def cmd_cd(args: list[str]) -> str:
    """Заглушка cd: возвращает имя команды и аргументы."""
    return f"cd: {args}"


def cmd_exit(args: list[str]) -> str:
    """Бросает исключение, которое будет обработано GUI."""
    if args:
        return "exit: too many arguments."

    raise ExitRequest()


COMMANDS = {
    "cd": cmd_cd,
    "ls": cmd_ls,
    "exit": cmd_exit
}


def execute(line: str) -> str:
    """Выполняет введённую строку и возвращает текст для вывода."""
    try:
        command_line = parse_command(line)
    except ParseError as e:
        return str(e)

    if not command_line:
        return ""

    command = COMMANDS.get(command_line[0])

    if command is None:
        return f"Command {command_line[0]} not found."

    return command(command_line[1:])
