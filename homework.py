import os
import logging
import requests
import sys
import time
from http import HTTPStatus

import telegram.ext
from dotenv import load_dotenv

from exceptions import EmptyAPIResponse, HttpStatusNotOK, TokensAccessError

load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
logger.addHandler(handler)


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

error_message = None


def check_tokens():
    """Проверяется доступность переменных окружения."""
    tokens_for_check = (PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID)
    if not all(tokens_for_check):
        logging.critical(
            'Переменные окружения недоступны.')
        raise TokensAccessError('Переменные окружения недоступны.')


def get_api_answer(timestamp):
    """Делается запрос к эндпоинту API-сервиса."""
    data_for_request = {
        'ENDPOINT': ENDPOINT,
        'HEADERS': HEADERS,
        'payload': {'from_date': timestamp},
    }
    logging.debug('Запрос к эндпоинту {ENDPOINT} API-сервиса '
                  'c данными заголовка {HEADERS} и параметрами '
                  '{payload} отправлено.'.format(**data_for_request))
    try:
        homework_statuses = requests.get(
            data_for_request['ENDPOINT'],
            headers=data_for_request['HEADERS'],
            params=data_for_request['payload']
        )
    except requests.exceptions.RequestException as error:
        error_message = (f'Сбой в работе программы: Эндпоинт {ENDPOINT} '
                         f'недоступен. Код ответа API: {error}.')
    homework_status_code = homework_statuses.status_code
    if homework_status_code != HTTPStatus.OK:
        raise HttpStatusNotOK('Статус ответа API не 200, '
                              f'а {homework_statuses.status_code}')
    return homework_statuses.json()


def check_response(response):
    """Проверяется ответ API на соответствие документации API сервиса."""
    if isinstance(response, dict):
        try:
            homeworks = response['homeworks']
        except EmptyAPIResponse('В ответе API домашки нет ключа `homeworks`.'):
            error_message = ('В ответе API домашки нет ключа `homeworks`.')
        if not isinstance(homeworks, list):
            error_message = ('В ответе API домашки под ключом `homeworks` '
                             'данные приходят не в виде списка.')
            raise TypeError(error_message)
        if homeworks == []:
            return False
        return homeworks
    raise TypeError('В ответе API домашки `response` '
                    'по типу не является словарем.')


def parse_status(homework):
    """Извлекается информация о домашней работе и статус этой работы."""
    try:
        homework_name = homework['homework_name']
    except KeyError:
        error_message = ('В ответе API домашки нет ключа `homework_name`.')
    try:
        status = homework['status']
        verdict = HOMEWORK_VERDICTS[status]
    except KeyError:
        error_message = ('В ответе API домашки возвращает '
                         'недокументированный статус домашней '
                         'работы либо домашку без статуса.')
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def send_message(bot, message):
    """Отправляется сообщение в Telegram чат."""
    logging.debug('Отправляется сообщение в Telegram.')
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.debug('Cообщение в Telegram отправлено.')
    except telegram.error.TelegramError as error:
        logging.error('При отправке сообщения в Telegram '
                      f'произошла ошибка {error}')


def main():
    """Основная логика работы бота."""
    check_tokens()
    previous_status = None
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = 0
    while True:
        try:
            response = get_api_answer(timestamp)
            homeworks = check_response(response)
            if homeworks:
                homework = homeworks[0]
                new_status = parse_status(homework)
            else:
                message = 'Новые статусы в ответе API отсутствуют.'
                logging.DEBUG(message)
            if previous_status != new_status:
                send_message(bot, new_status)
                previous_status = new_status
        except Exception as error:
            message = (f'Сбой в работе программы: {error}.'
                       f'{error_message}')
            send_message(bot, message)
            logging.exception(message)
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s, %(module)s, %(lineno)d,'
               '%(funcName)s, %(levelname)s, %(message)s'
    )
    main()
