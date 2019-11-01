class SyQueryException(Exception):
    pass


class SynamicQueryParsingError(SyQueryException):
    """Raised when there is an error in lexing or parsing query string."""
