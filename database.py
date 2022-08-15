import psycopg2 # Библиотека для работы с PostgreSQL
from psycopg2 import extras
from time import sleep
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('DB')

class DB:

    def __init__(self, host, user, password, db_name):
        """ Конструктор """

        self.__host = host # Хост для соединения с БД
        self.__user = user # Имя пользователя
        self.__password = password # Пароль
        self.__db_name = db_name # Название БД
        self.__connection = None # Соединение

    def connection_with_db(self, timeout=60):
        """ Метод для установления соединения с БД """

        while timeout != 0:
            try:
                self.__connection = psycopg2.connect(
                    host=self.__host,
                    user=self.__user,
                    password=self.__password,
                    database=self.__db_name
                )
            except Exception as ex:
                logger.error(f'Failed to connect to database {self.__db_name}')
                timeout -= 1
                logger.info(f'Tries left: {timeout}')
                sleep(1)
            else:
                logger.debug('Database connection established')
                self.__connection.autocommit = True
                break

    def query_execute(self, query, params=(), fetch=False, ext=False):
        """
        Метод, выполняющий запрос к БД

        :param query: запрос к БД
        """

        if self.__connection:
            with self.__connection.cursor() as cur:
                try:
                    if ext:
                        extras.execute_batch(cur, query, params)
                    else:
                        cur.execute(query, params)

                    if fetch:
                        res = cur.fetchone()
                        return res
                except Exception as e:
                    logger.error(f'An exception occurred: {e}')
                    self.connection_close()
        else:
            logger.warning('Unable to query the database because not connected to it')

    def connection_close(self):
        """ Метод, закрывающий соединение с БД """

        if self.__connection:
            self.__connection.close()
            logger.debug('Database connection closed')