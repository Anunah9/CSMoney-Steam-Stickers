from os import path, remove
import sqlite3
import wget
import requests
import pandas as pd


def item_data(func):
    def get_item_statistic(*args):
        self, item_name = args
        query = f"SELECT * FROM test WHERE name = '{item_name}'"
        self.data = self.con.execute(query).fetchall()
        func(*args)
    return get_item_statistic


class DatabaseTM:
    con = None
    cur = None

    def __init__(self):
        self.path_to_db = path.join(path.curdir, 'db') + path.sep
        self.__db_name = self.__get_name_db_csgo_tm__()
        self.con = sqlite3.connect(self.path_to_db + 'items_on_tm.db', check_same_thread=False)
        self.cur = self.con.cursor()

    @staticmethod
    def __get_name_db_csgo_tm__():
        url = 'https://market.csgo.com/itemdb/current_730.json'
        response = requests.get(url).text.split('"')
        __db_name = response[5]
        return __db_name

    def __get_db_from_csgo_tm__(self):
        url = f'https://market.csgo.com/itemdb/{self.__db_name}'
        wget.download(url, self.path_to_db)

    def __csv_converter__(self):
        data = pd.read_csv(self.path_to_db + self.__db_name, index_col=False, sep=";")
        df = pd.DataFrame(data)
        df.head()
        df.pop('c_base_id')
        df.pop('c_rarity')
        df.pop('c_name_color')
        df.pop('c_stickers')
        df.pop('c_slot')
        df.pop('c_offers')
        df.pop('c_price_updated')
        df.pop('c_quality')
        df.pop('c_heroid')
        df.pop('c_pop')

        self.__to_database__(df)

    def __to_database__(self, df):
        try:
            self.cur.execute("""drop table items""")

        except sqlite3.OperationalError:
            print('Таблицы нет')
        df.to_sql('items', self.con)

    def full_update_db(self):
        """На сайте БД обновляется раз в минуту, примерно на 15 секунде минуты"""
        self.__get_db_from_csgo_tm__()
        db_file = self.path_to_db + self.__db_name

        self.__csv_converter__()
        remove(db_file)
        print('Готово')

    def get_prices(self, market_hash_name):
        """Возвращает список кортежей типа (price, classid)"""
        query = f'SELECT c_price, c_classid FROM test WHERE c_market_hash_name = "{market_hash_name}"'
        data = self.cur.execute(query)
        data = data.fetchall()
        return data

    def get_min_price(self, market_hash_name):
        """Возвращает кортеж (price, classid) предмета с минимальной ценой"""

        query = f'SELECT c_price, c_classid FROM items WHERE c_market_hash_name = "{market_hash_name}" GROUP BY ' \
                f'c_price'
        min_price = self.cur.execute(query).fetchone()
        return min_price
