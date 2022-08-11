import psycopg2 # Библиотека для работы с PostgreSQL
from psycopg2 import extras

class DB:

    def __init__(self, host, user, password, db_name):
        """ Конструктор """

        self.__host = host # Хост для соединения с БД
        self.__user = user # Имя пользователя
        self.__password = password # Пароль
        self.__db_name = db_name # Название БД
        self.__connection = None # Соединение

    def connection_with_db(self):
        """ Метод для установления соединения с БД """

        # docker run - d - -network = host \
        # - e "DB_DBNAME=your_db" \
        # - e "DB_PORT=5432" \
        # - e "DB_USER=your_db_user" \
        # - e "DB_PASS=your_db_password" \
        # - e "DB_HOST=127.0.0.1" \
        # --name foobar foo / bar

        try:
            self.__connection = psycopg2.connect(
                host=self.__host,
                user=self.__user,
                password=self.__password,
                database=self.__db_name
            )
        except Exception as ex:
            print(f'[INFO] Не удалось подключиться к базе данных {self.__db_name}, возникло исключение: {ex}')
        else:
            print(f'[INFO] Соединение с базой данных {self.__db_name} установлено')
            self.__connection.autocommit = True

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
                        res = cur.fetchall()
                        return res
                except Exception:
                    self.connection_close()
        else:
            print('[INFO] Невозможно выполнить запрос к базе данных, т.к. соединение с ней не установлено')

    def connection_close(self):
        """ Метод, закрывающий соединение с БД """

        if self.__connection:
            self.__connection.close()
            print(f'[INFO] Соединение с базой данных {self.__db_name} закрыто')