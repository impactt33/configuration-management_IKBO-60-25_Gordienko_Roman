from pydantic import BaseModel

class Dependency(BaseModel):
    package_name: str
    dependencies: list[Dependency]