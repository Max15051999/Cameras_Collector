import requests  # Библиотека для отправки запросов
from bs4 import BeautifulSoup  # Библиотека для парсинга HTML-страниц
import re  # Библиотека для работы с регулярными выражениями
from time import time  # Библиотека для работы со временем

from database import DB  # Класс базы данных
from config import HOST, USERNAME, PASSWORD, DB_NAME, TABLE_NAME  # Настройки для соединения с базой данных

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/79.0.3945.88 Safari/537.36'
}  # Заголовки


def get_cameras_info(url: str):
    """
    Функция, получающая информацию о названиях камер и их координатах

    :param url: адрес, с которого будет парситься информация

    :return (list_cameras_names, list_cameras_coords): список названий камер и список координат камер
    """

    try:
        response = requests.get(url=url, headers=HEADERS)  # Посылаем get-запрос на сервер
    except requests.exceptions.ConnectionError as e:
        print(f'[INFO] Возникло исключение: {e}')
        return None
    else:
        if response.status_code == 200: # Если ответ от сервера получен

            soup = BeautifulSoup(response.text, 'html.parser')  # Получаем HTML-разметку страницы

            script_text = soup.find('div', id='list').find(
                'script').text  # Находим блок div с индексом list и берём из него текст тега script

            list_cameras_names = re.findall(r'hintContent: "(.*?)"',
                                            script_text)  # Находим все названия камер в тексте скрита
            list_cameras_coords = re.findall(r'coordinates: \[(.*?)]',
                                             script_text)  # Находим все координаты камер в тексте скрипта

            items = [] # Список элементов

            id = 1 # Уникальный идентификатор записи

            for camera, coords in zip(list_cameras_names, list_cameras_coords):
                lat, lon = float(coords.split(',')[0]), float(coords.split(',')[1]) # Вычисление широты и долготы камеры
                items.append((id, camera, coords, lon, lat)) # Добавление в список элементов кортежа с данными камеры
                id += 1

            return items

        else:
            print(f'[INFO] Соединение с сервером, находящимся по адресу {url} не установлено')
            return None

def save_info_in_DB():
    """ Функция, сохраняющая информацию о камерах и их координатах в БД """

    items = get_cameras_info(
        url='https://xn--90adear.xn--p1ai/milestones?all=true')  # Получение списка кортежей с данными о камерах

    if items:
        db = DB(host=HOST, user=USERNAME, password=PASSWORD, db_name=DB_NAME)  # Создание экземпляра класса DB
        db.connection_with_db()  # Установление соединения с БД

        # Ошибка: В docker нет postgis, соответственно нет типа GEOMETRY
        query = f""" CREATE TABLE IF NOT EXISTS {TABLE_NAME}(id INTEGER PRIMARY KEY, name VARCHAR(255),
            coords VARCHAR(255), geo GEOMETRY NULL); """

        db.query_execute(query=query)  # Создание таблицы cameras_info в БД

        amount_data_in_db = db.query_execute(f""" SELECT COUNT(id) FROM {TABLE_NAME}; """, fetch=True) # Количество записей в БД

        print(f'In DB {amount_data_in_db}')

        if amount_data_in_db[0] != 0: # Если есть данные в БД
            query = f""" INSERT INTO {TABLE_NAME}(id, name, coords, geo) 
                VALUES (%s, %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326)) 
                ON CONFLICT(id) DO UPDATE SET coords=EXCLUDED.coords, geo=EXCLUDED.geo;  """

            db.query_execute(query=query, params=items, ext=True) # Обновить данные если необходимо

        else:
            query = f""" INSERT INTO {TABLE_NAME}(id, name, coords, geo) VALUES(%s, %s, %s, ST_SetSRID(ST_MakePoint(
            %s, %s), 4326)); """

            db.query_execute(query=query, params=items, ext=True) # Вставить данные в БД

        db.connection_close()  # Закрытие соединения с БД


def main():
    """ Точка входа """

    save_info_in_DB()


if __name__ == '__main__':
    start = time()  # Время до запуска функции
    main()
    print(f'[INFO] Функция работала: {time() - start}')