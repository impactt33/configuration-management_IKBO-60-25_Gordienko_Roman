from hw2.core.exceptions import AppError, ParseError

class MissingRequiredArgumentError(ParseError):
    pass

class PackageNotFoundError(ParseError):
    pass

class VersionNotFoundError(ParseError):
    """Запрошенная или подходящая версия отсутствует в репозитории."""


class RepositoryFileError(ParseError):
    """Файл тестового репозитория недоступен или имеет неверный формат."""


class CyclicDependencyError(AppError):
    """Цикл не позволяет поставить каждую зависимость раньше её родителя."""


class VisualizationError(AppError):
    """Ошибка рендеринга D2 или открытия полученного изображения."""
