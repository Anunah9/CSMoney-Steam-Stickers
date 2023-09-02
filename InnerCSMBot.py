import pprint
import statistics
import time
from typing import Type
from urllib.parse import quote

import telebot
import urllib3

from utils.CSMoneyAPI import CSMMarketMethods
import requests


def get_items_from_csm(offset, min_price=0.0, max_price=100000.0):
    return csmoney_acc.get_items(offset=offset, min_price=min_price, max_price=max_price)


class Sticker:
    def __init__(self, sticker):
        self.name = sticker['name']
        self.overprice = sticker['overprice']
        self.position = sticker['position']
        self.price = sticker['price']
        self.wear = sticker['wear']


class Item:
    def __init__(self, item):
        self.appId = item.get("appId")
        self.assetId = item.get("assetId")
        self.collection = item.get("collection")
        self.float = item.get("float")
        self.fullName = item.get("fullName")
        self.fullSlug = item.get("fullSlug")
        self.hasHighDemand = item.get("hasHighDemand")
        self.hasTradeLock = item.get("hasTradeLock")
        self.id = item.get("id")
        self.img = item.get("img")
        self.inspect = item.get("inspect")
        self.nameId = item.get("nameId")
        self.overpay = item.get("overpay")
        self.overprice = item.get("overprice")
        self.pattern = item.get("pattern")
        self.preview = item.get("preview")
        self.price = item.get("price")
        self.defaultPrice = None
        self.priceWithBonus = item.get("priceWithBonus")
        self.quality = item.get("quality")
        self.rank = item.get("rank")
        self.rarity = item.get("rarity")
        self.screenshot = item.get("screenshot")
        self.shortName = item.get("shortName")
        self.steamId = item.get("steamId")
        self.steamImg = item.get("steamImg")
        self.stickers = item.get("stickers")
        if self.hasTradeLock:
            self.tradeLock = item.get("tradeLock")
        self.type = item.get("type")
        self.userId = item.get("userId")
        self.item_name = item['fullName']
        self.overpay = item['overpay']
        self.csm_price = item['price']
        self.stickers = item['stickers']
        self.__convert_stickers()

    def __convert_stickers(self):
        stickers_result = []

        for sticker in self.stickers:
            if not sticker:
                continue
            stickers_result.append(Sticker(sticker))
        self.stickers = stickers_result

    def check_strick(self):
        element_count = {}
        for item in self.stickers:
            name = item.name
            if name in element_count:
                element_count[name]['count'] += 1
            else:
                element_count[name] = {'count': 1, 'price': item.price}

        # Фильтруем элементы, оставляем только те, что встречаются 3 и более раз
        filtered_elements = {'Strick': info for name, info in element_count.items() if info['count'] >= 3}
        if 'Strick' in filtered_elements:
            return True
        else:
            return False


class Profit:
    def __init__(self):
        self.overprice_from_me = None
        self.result_price = None
        self.profit = None
        self.real_procent_overpay = None
        self.pred_procent_overpay = None
        self.middle_price = None

    def get_profit_strick(self, item: Item):
        self.overprice_from_me = float(item.stickers[0].price * 0.5 * len(item.stickers))
        self.result_price = item.defaultPrice + self.overprice_from_me
        self.profit = self.result_price / item.price - 1

    def get_profit(self, item: Item):
        pass

    def pred_filter(self,   price_):
        if self.pred_procent_overpay < 0.1 or self.pred_procent_overpay > 0.3:
            return False
        elif price_ < 2.5:
            return False
        elif self.real_procent_overpay > 0.7:
            return False
        else:
            return True

    def post_filter(self):
        if self.middle_price * 1.1 < self.result_price:
            return False
        else:
            return True


def create_url(item):
    url = 'https://cs.money/csgo/trade/'
    params = {
        'search': quote(item.item_name),
        'minPrice': item.price,
        'maxPrice': item.price + 0.01,
        'hasRareStickers': 'true',
        'hasTradeLock': 'true'
    }
    query_string = '&'.join([f'{key}={value}' for key, value in params.items()])
    full_url = f'{url}?{query_string}'
    return full_url


def item_handler(item: Item):

    url = create_url(item)
    profit_item = Profit()
    overpay = item.overpay['stickers']
    buy_price = item.csm_price
    profit_item.pred_procent_overpay = overpay / buy_price

    def_price = csmoney_acc.get_def_price(item.id)
    profit_item.real_procent_overpay = buy_price / def_price - 1
    price_history = csmoney_acc.get_price_history(item.nameId, 30)
    price_history = list(map(lambda x: x['price'], price_history))
    if not price_history:
        return False
    profit_item.middle_price = statistics.mean(price_history)
    print(price_history)
    print(profit_item.middle_price)
    if not profit_item.pred_filter(buy_price):
        print('Предмет не подходит')
        return False

    item.defaultPrice = def_price
    have_strick = item.check_strick()
    print(item.preview)
    if have_strick:
        profit_item.get_profit_strick(item)

        message = ''
        message += '----------------------------------\n'
        message += item.item_name + '\n'
        message += f'Цена покупки: {buy_price}\n'
        message += f'Стандартная цена без наценок: {def_price}\n'
        message += f'Overpay от CSMoney за наклейки: {overpay}\n'
        message += f'Наценка от CSMoney за наклейки: {profit_item.pred_procent_overpay:.2%}\n'
        message += f'Реальная переплата от CSMoney: {profit_item.real_procent_overpay:.2%}\n'
        message += f'Цена одного стикера: {item.stickers[0].price}\n'
        message += f'Количество стикеров: {len(item.stickers)}\n'
        message += f'Моя наценка: {profit_item.overprice_from_me:.2}\n'
        message += f'Цена продажи: {profit_item.result_price:.2}\n'
        message += f'Средняя цена продажи: {float(profit_item.middle_price):.2}\n'
        message += f'Профит: {profit_item.profit:.2%}\n'
        message += url
        print(message)
        print('Strick: ', have_strick)
        if not profit_item.post_filter():
            print('Предмет не подходит')
            return False
        if profit_item.profit > 0:
            bot.send_photo(368333609, item.img, message)

    else:
        profit_item.get_profit(item)
        print('Strick: ', have_strick)


def main():
    for offset in range(0, 360, 60):
        print(offset)
        items = get_items_from_csm(offset, min_price=2.5, max_price=20)
        for item in items:
            item_info = Item(item)
            if not item_handler(item_info):
                continue
            time.sleep(1)
        time.sleep(2)


if __name__ == '__main__':
    bot = telebot.TeleBot('5096520863:AAHHvfFpQTH5fuXHjjAfzYklNGBPw4z57zA')
    csmoney_acc = CSMMarketMethods(None)
    main()


