from hw2.core.exceptions import ParseError

class MissingRequiredArgumentError(ParseError):
    pass

class PackageNotFoundError(ParseError):
    pass

class VersionNotFoundError(ParseError):
    pass