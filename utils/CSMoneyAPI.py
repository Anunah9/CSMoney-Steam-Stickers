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


def get_price(market_hash_name):
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
    default_price = __get_def_price(item_id)
    return default_price


def __get_def_price(item_id):
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
    rub_price = round(utils.Utils.change_currency(default_price), 2)
    return rub_price


def get_sticker_overpay(market_hash_name, sticker, csm_price):
    url = 'https://inventories.cs.money/5.0/load_bots_inventory/730'
    slot = sticker['slot']
    sticker_name = sticker['name']
    params = {
        'maxPrice': (csm_price * 2)/80,
        'limit': 60,
        'offset': 0,
        'priceWithBonus': 30,
        'isMarket': 'false',
        'sort': 'price',
        f'stickerName1':  sticker_name,
        'withStack': 'true'
    }
    response = requests.get(url, params=params)
    if response.status_code != 200:
        print('Get sticker overpay', response)
    return response.json()
