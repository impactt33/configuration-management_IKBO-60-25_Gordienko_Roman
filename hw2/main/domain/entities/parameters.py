"""Параметры CLI и проверка пользовательского ввода."""

from pathlib import Path
from urllib.parse import urlsplit

from packaging.requirements import InvalidRequirement, Requirement
from packaging.version import InvalidVersion, Version
from pydantic import (
    BaseModel, ConfigDict, Field, field_validator, model_validator,
)


class PackageManagerParameters(BaseModel):
    """Задаёт источник пакетов и ограничения обхода."""

    model_config = ConfigDict(validate_by_name=True)

    name: str = Field(alias="--name", description="Имя пакета; можно с extras")
    repo_url: str = Field(
        default="https://pypi.org/simple/", alias="--repo",
        description="URL Simple API или путь к JSON при --test-mode",
    )
    test_mode: bool = Field(
        default=False,
        alias="--test-mode",
        json_schema_extra={"action": "store_true"},
        description="Читать локальный репозиторий без сетевых запросов",
    )
    version: str = Field(alias="--version", description="Версия пакета")
    max_depth: int = Field(
        ge=0, alias="--max-depth", default=3,
        description="Максимальная глубина: корень 0, прямые зависимости 1",
    )
    filter: str = Field(
        default="", alias="--filter",
        description="Исключать имена с этой подстрокой без учёта регистра",
    )
    output_format: str = Field(
        default="json", alias="--format",
        json_schema_extra={"choices": ["json", "order", "d2"]},
        description="Вывод: граф JSON, порядок загрузки или диаграмма D2",
    )
    output: str = Field(
        default="", alias="--output",
        description="Сохранить вывод; для D2 путь .svg включает рендеринг",
    )
    show: bool = Field(
        default=False, alias="--show",
        json_schema_extra={"action": "store_true"},
        description="Открыть SVG в браузере; нужен --format d2 --output *.svg",
    )

    @model_validator(mode="after")
    def validate_output(self) -> "PackageManagerParameters":
        """Проверяет сочетания опций и защищает входной файл от перезаписи."""
        is_svg = Path(self.output).suffix.lower() == ".svg"
        if self.show and not (self.output_format == "d2" and is_svg):
            raise ValueError("--show требует --format d2 и --output *.svg")
        if is_svg and self.output_format != "d2":
            raise ValueError("--output *.svg требует --format d2")
        if self.output and self.test_mode:
            paths = [Path(self.output).resolve()]
            if is_svg:
                paths.append(Path(self.output).with_suffix(".d2").resolve())
            if Path(self.repo_url).resolve() in paths:
                raise ValueError("--output не должен перезаписывать --repo")
        return self

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        """Отделяет имя и extras от версии и маркеров окружения."""
        try:
            requirement = Requirement(value.strip())
        except InvalidRequirement as error:
            raise ValueError("некорректное имя пакета") from error
        if requirement.specifier or requirement.url or requirement.marker:
            raise ValueError("укажите имя пакета; версия задаётся --version")
        return str(requirement)

    @field_validator("version")
    @classmethod
    def validate_version(cls, value: str) -> str:
        """Проверяет версию, сохраняя выбранную пользователем запись."""
        value = value.strip()
        try:
            Version(value)
        except InvalidVersion as error:
            raise ValueError("некорректная версия пакета") from error
        return value

    @field_validator("repo_url")
    @classmethod
    def validate_source(cls, value: str) -> str:
        """Сохраняет пробелы внутри пути, но отклоняет пустой источник."""
        value = value.strip()
        if not value:
            raise ValueError("репозиторий не может быть пустым")
        return value

    @model_validator(mode="after")
    def validate_repository_url(self) -> "PackageManagerParameters":
        """Проверяет HTTP-адрес только при работе с сетевым источником."""
        if self.test_mode:
            return self
        url = self.repo_url
        if "://" not in url:
            url = f"https://{url}"
        parsed = urlsplit(url)
        if (
            parsed.scheme not in {"http", "https"} or not parsed.hostname
            or any(character.isspace() for character in url)
            or parsed.query or parsed.fragment
        ):
            raise ValueError("--repo: нужен HTTP(S)-адрес Simple API")
        return self
