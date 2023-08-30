class HttpStatusNotOK(Exception):
    """Возвращается код, отличный от 200."""

    pass


class KeyExistingException(Exception):
    """Ошибка наличия ключа."""

    pass


class ValueExistingException(Exception):
    """Ошибка доступности обязательных переменных окружения."""

    pass
