class ValueExistingException(Exception):
    """Ошибка доступности обязательных переменных окружения."""

    pass


class KeyExistingException(Exception):
    """Ошибка наличия ключа."""

    pass
