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

    # try:
    #     response = requests.get(url=url, headers=HEADERS)  # Посылаем get-запрос на сервер
    # except requests.exceptions.ConnectionError as e:
    #     print(f'[INFO] Возникло исключение: {e}')
    #     return None
    # else:
    #     if response.status_code == 200: # Если ответ от сервера получен
    #
    #         soup = BeautifulSoup(response.text, 'html.parser')  # Получаем HTML-разметку страницы
    #
    #         script_text = soup.find('div', id='list').find(
    #             'script').text  # Находим блок div с индексом list и берём из него
    #         # текст тега script

            # list_cameras_names = re.findall(r'hintContent: "(.*?)"',
            #                                 script_text)  # Находим все названия камер в тексте скрита
            # list_cameras_coords = re.findall(r'coordinates: \[(.*?)]',
            #                                  script_text)  # Находим все координаты камер в тексте скрипта

    list_cameras_names = [
        '001 Костромская обл.,г.Кострома, ул.Октябрьская, 54',
        '002 Костромская обл.,г.Кострома, ул.Октябрьская, 54',
        '002 Передвижной комплекс',
        '003 Передвижной комплекс',
    ] # Тестовые данные

    list_cameras_coords = [
        '35.74315200287, 55.966534473812',
        '51.74315200287, 40.966534473812',
        '70.977720773815, 85.381273541438',
        '75.977720773815, 90.381273541438',
    ] # Тестовые данные

    items = [] # Список элементов

    for camera, coords in zip(list_cameras_names, list_cameras_coords):
        lat, lon = float(coords.split(',')[0]), float(coords.split(',')[1]) # Вычисление широты и долготы камеры
        items.append((camera, coords, lon, lat)) # Добавление в список элементов кортежа с данными камеры

    return items

        # else:
        #     print(f'[INFO] Соединение с сервером, находящимся по адресу {url} не установлено')
        #     return None

def check_update_data(db, items, data_in_db):
    """ Функция, проверяющая и обновляющая данные в БД

    :param db: Ссылка на экземпляр класса DB для взаимодействия с базой данных
    :param items: Список кортежей с данными о камерах, полученный с сайта
    :param data_in_db: Список кортежей с данными о камерах, взятых из БД

    """

    get_data = len(items)  # Вычисление длины списка с кортежами

    if len(data_in_db) != get_data:  # Если появились новые камеры
        data_in_db_list = [e for l in data_in_db for e in l]  # Получить список из списка кортежей

        new_data = [item for item in items if item[0] not in data_in_db_list]  # Список добавленных камер

        query = f""" INSERT INTO {TABLE_NAME}(name, coords, geo) VALUES(%s, %s, ST_SetSRID(ST_MakePoint(%s, 
                        %s), 4326)); """  # Запрос для добавления информации о камерах в БД

        db.query_execute(query=query, params=new_data, ext=True)  # Добавление информации о камерах в БД

    change_count = 0  # Количество обновленных записей в БД

    for i in range(get_data):
        new_coords = items[i][1]  # Получение координат камеры с сайта

        try:
            if new_coords != data_in_db[i][2]:  # Если координаты камеры с сайта не совпадают с координатами
                # камеры в БД
                id = data_in_db[i][0]  # Получить id этой камеры

                query = f""" UPDATE {TABLE_NAME} SET coords = (%s), geo = (ST_SetSRID(ST_MakePoint(%s, %s), 4326)) WHERE id = %s; """

                db.query_execute(query=query, params=(new_coords, items[i][2], items[i][3], id,))  # Обновить
                # координаты и геометрию точки камеры с данным id

                change_count += 1  # Инкремент количества изменений
        except IndexError:
            continue

    if change_count > 0:
        print(f'[INFO] В таблице cameras_info обновлено записей: {change_count}')
    else:
        print('[INFO] В таблице cameras_info все данные актуальны')


def save_info_in_DB():
    """ Функция, сохраняющая информацию о камерах и их координатах в БД """

    items = get_cameras_info(
        url='https://xn--90adear.xn--p1ai/milestones?all=true')  # Получение списка кортежей с данными о камерах

    if items:
        db = DB(host=HOST, user=USERNAME, password=PASSWORD, db_name=DB_NAME)  # Создание экземпляра класса DB
        db.connection_with_db()  # Установление соединения с БД

        query = f""" CREATE TABLE IF NOT EXISTS {TABLE_NAME}(id SERIAL PRIMARY KEY, name VARCHAR(255),
            coords VARCHAR(255), geo GEOMETRY NULL); """

        db.query_execute(query=query)  # Создание таблицы cameras_info в БД

        data_in_db = db.query_execute(f""" SELECT id, name, coords FROM {TABLE_NAME} ORDER BY id; """, fetch=True) # Взять поля id
        # и coords всех камер из БД. Ответ будет в виде списка кортежей

        if data_in_db: # Если есть данные в БД
            check_update_data(db=db, items=items, data_in_db=data_in_db) # Проверить и обновить данные

        else:
            query = f""" INSERT INTO {TABLE_NAME}(name, coords, geo) VALUES(%s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326)); """

            db.query_execute(query=query, params=items, ext=True) # Вставить данные в БД

        db.connection_close()  # Закрытие соединения с БД


def main():
    """ Точка входа """

    save_info_in_DB()


if __name__ == '__main__':
    start = time()  # Время до запуска функции
    main()
    print(f'[INFO] Функция работала: {time() - start}')