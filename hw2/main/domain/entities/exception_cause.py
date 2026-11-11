from pydantic import BaseModel


class ExceptionCause(BaseModel):
    status_code: int
    cause: str