"""Создаёт CLI из полей Pydantic и выводит понятные ошибки ввода."""

import argparse
from collections.abc import Sequence

from pydantic import BaseModel, ValidationError

from hw2.core.exceptions import UnsupportedTypeError


def nonempty(value: str) -> str:
    """Отклоняет пустую строку без удаления пробелов внутри значения."""
    value = value.strip()
    if not value:
        raise argparse.ArgumentTypeError("значение не может быть пустым")
    return value


def _add_model_arguments(
    parser: argparse.ArgumentParser, arguments_model: type[BaseModel],
) -> None:
    """Переносит настройки полей в argparse, не меняя модель."""
    for param_name, field_info in arguments_model.model_fields.items():
        extra = field_info.json_schema_extra
        if extra is not None and not isinstance(extra, dict):
            raise TypeError("json_schema_extra must be a valid dict")
        options = dict(extra or {})
        options["required"] = field_info.is_required()
        options.setdefault("help", field_info.description)
        if options.get("action", "store") == "store":
            options.setdefault("type", field_info.annotation)
        parser.add_argument(
            field_info.alias or f"--{param_name.replace('_', '-')}",
            dest=param_name, **options,
        )


def parse_command_line[T: BaseModel](
    arguments_model: type[T], argv: Sequence[str] | None = None,
) -> T:
    """Возвращает проверенную модель; ошибки CLI завершают запуск с кодом 2."""
    if not issubclass(arguments_model, BaseModel):
        raise UnsupportedTypeError(arguments_model)
    parser = argparse.ArgumentParser(description="Граф зависимостей Python")
    _add_model_arguments(parser, arguments_model)
    args = {
        name: value
        for name, value in vars(parser.parse_args(argv)).items()
        if value is not None
    }
    try:
        return arguments_model(**args)
    except ValidationError as error:
        messages = []
        for issue in error.errors():
            field = None
            if issue["loc"]:
                field = arguments_model.model_fields.get(issue["loc"][0])
            name = field.alias if field is not None else "параметры"
            messages.append(f"{name}: {issue['msg']}")
        parser.error("; ".join(messages))
