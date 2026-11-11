import argparse

from typing import Any
from pydantic import BaseModel

from hw2.core.exceptions import UnsupportedTypeError, EmptyArgumentError

SUPPORTED_TYPES = [BaseModel]

def nonempty(value: str) -> str:
    value = value.replace(" ", "")

    if not value:
        raise EmptyArgumentError()

    return value

def parse_command_line[T: Any](arguments_model: type[T]) -> T:
    if not any(issubclass(arguments_model, subclass) for subclass in SUPPORTED_TYPES):
        raise UnsupportedTypeError(arguments_model)

    parser = argparse.ArgumentParser()

    if issubclass(arguments_model, BaseModel):
        for param_name, field_info in arguments_model.model_fields.items():
            options = field_info.json_schema_extra

            if options is None:
                options = {"type": nonempty}
            if not isinstance(options, dict):
                raise TypeError("json_schema_extra must be a valid dict")

            options["required"] = field_info.is_required()

            parser.add_argument(
                field_info.alias or param_name,
                dest=param_name,
                **options
            )

    args = {}
    for name, value in vars(parser.parse_args()).items():
        if value is None:
            continue

        args[name] = value

    return arguments_model(**args)