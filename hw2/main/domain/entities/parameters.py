from pydantic import BaseModel, Field, ConfigDict


class PackageManagerParameters(BaseModel):
    model_config = ConfigDict(validate_by_name=True)

    name: str = Field(alias="--name")
    repo_url: str = Field(default="https://pypi.org/", alias="--repo")
    test_mode: bool = Field(
        default=False,
        alias="--test-mode",
        json_schema_extra={"action": "store_true"}
    )
    version: str = Field(alias="--version")
    max_depth: int = Field(ge=1, le=5, alias="--max-depth", default=3)
    filter: str = Field(default="", alias="--filter")
