class AppError(Exception):
    pass

class ParseError(AppError):
    pass

class HttpError(AppError):
    def __init__(self, status: int, url: str) -> None:
        self.status = status
        self.url = url
        super().__init__(f"HTTP {status} for {url}")

class UnsupportedTypeError(ParseError):
    def __init__(self, arg_type: type) -> None:
        super().__init__(f"Unsupported type {arg_type.__name__}")

class EmptyArgumentError(ParseError):
    pass