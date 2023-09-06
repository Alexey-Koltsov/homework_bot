class EmptyAPIResponse(Exception):
    """Возвращается пустой словарь ответа API."""

    pass


class HttpStatusNotOK(Exception):
    """Возвращается код, отличный от 200."""

    pass


class TokensAccessError(Exception):
    """Переменные окружения недоступны."""

    pass
