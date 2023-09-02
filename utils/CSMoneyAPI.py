import datetime

import requests

import utils.Utils

"""
Модуль для работы с кс мани - набор функций для обеспечения работы модуля отслеживания:
-Получить цену предмета
-Получить переплату за наклейку - эта функция довольно комплексная потому что заранее узнать переплату за стикер нельзя, 
 поэтому эту функцию надо разбить на 3 последовательных проверки:
    -Проверяем есть ли точно такой же предмет как у нас(с теми же наклейками и тем же скином)
    -Проверяем есть ли просто прдметы с такими же наклейками
    -Проверяем переплату за каждую наклейку в отдельности на разных слотах и разных скинах
-Получить переплату за float - ну тут надо просто искать такой же предмет с таким же float"""


class CSMMarketMethods:
    cookies = None
    currency = utils.Utils.Currensy()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/114.0.0.0 YaBrowser/23.7.2.767 Yowser/2.5 Safari/537.36'
    }

    def __init__(self, _cookies):
        self.cookies = _cookies

    @staticmethod
    def get_items(min_price=0, max_price=1000, offset=0):
        url = 'https://inventories.cs.money/5.0/load_bots_inventory/730'
        params = {
            'hasRareStickers': 'true',
            'hasTradeLock': 'true',
            'limit': 60,
            'maxPrice': max_price,
            'minPrice': min_price,
            'offset': offset,
            'order': 'asc',
            'sort': 'price',
            'withStack': 'true'
        }
        response = requests.get(url, params)
        if response.status_code != 200:
            print('Get items:', response)
        return response.json()['items']

    def get_price(self, market_hash_name):
        url = 'https://inventories.cs.money/5.0/load_bots_inventory/730'
        params = {
            'isMarket': 'false',
            'hasRareFloat': 'false',
            'hasRareStickers': 'false',
            'limit': 60,
            'name': market_hash_name,
            'offset': 0,
            'priceWithBonus': 30,
            'order': 'asc',
            'sort': 'price',
            'withStack': 'true'
        }

        response = requests.get(url, params=params)
        if response.status_code != 200:
            print('Get price CSMoney', response)
            return False
        item = response.json()
        if 'error' in item and item['error'] == 2:
            print('error 2')
            return False

        item = item['items'][0]
        item_id = item['id']
        default_price = self.get_def_price(item_id)
        rub_price = round(self.currency.change_currency(default_price), 2)
        return rub_price

    @staticmethod
    def get_def_price(item_id):
        url = 'https://cs.money/skin_info'
        params = {
            'appId': 730,
            'id': item_id,
            'isBot': 'true',
            'botInventory': 'true'
        }
        response = requests.get(url, params)
        if response.status_code != 200:
            print('Get skin info', response)
        default_price = response.json()['defaultPrice']

        return default_price

    @staticmethod
    def get_price_history(item_id, days):
        url = 'https://cs.money/market_sales'
        today = datetime.datetime.today()
        second_date = today - datetime.timedelta(days)
        params = {
            'appId': 730,
            'nameId': item_id,
            'startTime': second_date.timestamp()*1000,
            'endTime': today.timestamp()*1000
        }
        response = requests.get(url, params)

        if response.status_code != 200:
            print('Get price history:', response.status_code)
        return response.json()

    @staticmethod
    def get_sticker_overpay(market_hash_name, sticker, csm_price):
        url = 'https://inventories.cs.money/5.0/load_bots_inventory/730'
        slot = sticker['slot']
        sticker_name = sticker['name']
        params = {
            'maxPrice': (csm_price * 2) / 80,
            'limit': 60,
            'offset': 0,
            'priceWithBonus': 30,
            'isMarket': 'false',
            'sort': 'price',
            f'stickerName1': sticker_name,
            'withStack': 'true'
        }
        response = requests.get(url, params=params)
        if response.status_code != 200:
            print('Get sticker overpay', response)
        return response.json()

    def get_inventory(self):
        url = 'https://cs.money/3.0/load_user_inventory/730?'
        params = {
            'isPrime': 'false',
            'limit': 60,
            'noCache': 'true',
            'offset': 0,
            'order': 'desc',
            'sort': 'price',
            'withStack': 'true'
        }

        response = requests.get(url, params, cookies=self.cookies, headers=self.headers)
        if response.status_code != 200:
            print('Get inventory: ', response)
        return response.json()['items']

    def get_inventory_item_info(self, item_id):
        url = 'https://cs.money/skin_info?'
        params = {
            'appId': 730,
            'id': item_id,
            'isBot': 'false',
            'botInventory': 'false'
        }
        response = requests.get(url, params, headers=self.headers, cookies=self.cookies)
        if response.status_code != 200:
            print('Get inventory item info: ', response)
        elif 'error' in response.json():
            raise Exception(f"error: {response.json()['error']}")

        return response.json()
