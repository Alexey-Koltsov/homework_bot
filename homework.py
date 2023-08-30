import os
import logging
import requests
import sys
import telegram.ext
import time

from dotenv import load_dotenv
from http import HTTPStatus


from exceptions import HttpStatusNotOK

load_dotenv()

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s, %(levelname)s, %(message)s'
)
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


def check_tokens():
    """Проверяется доступность переменных окружения."""
    if PRACTICUM_TOKEN and TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        return True
    else:
        logging.critical(
            'Переменные окружения недоступны.')
        sys.exit('Переменные окружения недоступны.')


def get_api_answer(timestamp):
    """Делается запрос к эндпоинту API-сервиса."""
    payload = {'from_date': timestamp}
    try:
        homework_statuses = requests.get(
            ENDPOINT, headers=HEADERS, params=payload)
    except requests.exceptions.RequestException as error:
        logging.error(f'Сбой в работе программы: Эндпоинт {ENDPOINT} '
                      f'недоступен. Код ответа API: {error}.')
    homework_status_code = homework_statuses.status_code
    if homework_status_code != HTTPStatus.OK:
        raise HttpStatusNotOK('Статус ответа API не 200, '
                              f'а {homework_statuses.status_code}')
    return homework_statuses.json()


def check_response(response):
    """Проверяется ответ API на соответствие документации API сервиса."""
    try:
        homeworks = response['homeworks']
    except KeyError:
        logging.error('В ответе API домашки нет ключа `homeworks`.')
    if not isinstance(homeworks, list):
        logging.error('В ответе API домашки под ключом `homeworks` '
                      'данные приходят не в виде списка.')
        raise TypeError('В ответе API домашки под ключом `homeworks` '
                        'данные приходят не в виде списка.')
    if homeworks == []:
        return False
    return True


def parse_status(homework):
    """Извлекается информация о домашней работе и статус этой работы."""
    if homework != []:
        try:
            homework_name = homework['homework_name']
        except KeyError:
            logging.error('В ответе API домашки нет ключа `homework_name`.')
        try:
            status = homework['status']
            verdict = HOMEWORK_VERDICTS[status]
        except KeyError:
            logging.error('В ответе API домашки возвращает '
                          'недокументированный статус домашней '
                          'работы либо домашку без статуса.')
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def send_message(bot, message):
    """Отправляется сообщение в Telegram чат."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.debug('Сообщение отправлено.')
    except Exception:
        logging.error(message)


def main():
    """Основная логика работы бота."""
    check_tokens()
    previous_homework = None
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    while True:
        try:
            response = get_api_answer(timestamp)
            if check_response(response):
                if previous_homework != response['homeworks']:
                    homework = response['homeworks'][0]
                    message = parse_status(homework)
                    send_message(bot, message)
                    previous_homework = response['homeworks']
                else:
                    logging.DEBUG('Новые статусы в ответе API отсутствуют.')
        except Exception as error:
            message = f'Сбой в работе программы: {error}.'
            send_message(bot, message)
            logging.exception(message)
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
