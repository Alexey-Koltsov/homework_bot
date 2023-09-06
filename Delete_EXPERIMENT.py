"""
Технический файл.
УДАЛИТЬ ПЕРЕД ОТПРАВКОЙ НА РЕВЬЮ.
"""


ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': 'OAuth PRACTICUM_TOKEN'}

data_for_request = {
    'ENDPOINT': ENDPOINT,
    'HEADERS': HEADERS,
    'payload': {'from_date': 'timestamp'},
}
print('Запрос к эндпоинту {ENDPOINT} API-сервиса '
      'c данными заголовка {HEADERS} и параметрами '
      '{payload} отправлен.'.format(**data_for_request))
