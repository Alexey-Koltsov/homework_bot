import os
import requests
import telegram.ext
import time

from dotenv import load_dotenv
from http import HTTPStatus
from pprint import pprint

from exceptions import KeyExistingException, ValueExistingException

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN_ENV')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN_ENV')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID_ENV')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


consts_for_check = (
    ('PRACTICUM_TOKEN', PRACTICUM_TOKEN),
    ('TELEGRAM_TOKEN', TELEGRAM_TOKEN),
    ('TELEGRAM_CHAT_ID', TELEGRAM_CHAT_ID),
)

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens(args):
    """Проверяется доступность переменных окружения."""
    for const_name, const in args:
        if const is None:
            raise ValueExistingException(
                f'Переменная окружения {const_name} недоступна.')


def get_api_answer(timestamp):
    """Делается запрос к эндпоинту API-сервиса."""
    payload = {'from_date': timestamp}
    homework_statuses = requests.get(ENDPOINT, headers=HEADERS, params=payload)
    return homework_statuses.json()


def check_response(response):
    """Проверяется ответ API на соответствие документации API сервиса."""
    for key in response:
        if key not in ('homeworks', 'current_date'):
            raise KeyExistingException(
                f'Ответ содержит ключ {key}, '
                'отличный от current_date и homeworks.')


def parse_status(homework):
    """Извлекается информация о домашней работе и статус этой работы."""
    homework_name = homework['homeworks'][0]['homework_name']
    status = homework['homeworks'][0]['status']
    verdict = HOMEWORK_VERDICTS[status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def send_message(bot, message):
    """Отправляется сообщение в Telegram чат."""
    bot.send_message(TELEGRAM_CHAT_ID, message)


def main():
    """Основная логика работы бота."""
    # Проверяем доступность пременных окружения
    check_tokens(consts_for_check)
    previous_homeworks = None
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    while True:
        try:
            response = get_api_answer(1690412003)  # timestamp
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            ...
        check_response(response)
        if previous_homeworks != response['homeworks']:
            message = parse_status(response)
            send_message(bot, message)
            previous_homeworks = response['homeworks']
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
