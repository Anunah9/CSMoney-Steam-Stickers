import pprint
import time
from typing import Type
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
        self.item_name = item['fullName']
        self.overpay = item['overpay']
        self.csm_price = item['price']
        self.stickers = item['stickers']
        self.__convert_stickers()
        if 'tradelock' in item:
            self.tradelock = item['tradeLock']
        else:
            self.tradelock = 0
        self.userid = item['userId']

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


def get_profit(item: Item):
    print(item.item_name)
    print( item.stickers)
    print('get profit:', item.overpay)
    print(item.csm_price)
    print('Strick: False')


def get_profit_strick(item: Item):

    print(item.item_name)
    print(item.stickers)
    print(item.overpay)
    print(item.csm_price)
    print('Strick: True')


def pred_filter(item: Item):
    overpay = item.overpay['stickers']
    price = item.csm_price
    procent = round(overpay/price, 2)
    print('overpay в pred filter:', overpay)
    print('Наценка: ', procent)
    if procent < 0.1 or procent > 0.3:
        return False
    elif price < 2.5:
        return False
    else:
        return True


def main():
    for offset in range(0, 360, 60):
        items = get_items_from_csm(offset, min_price=2.5, max_price=20)
        for item in items:
            print('----------------------------------')
            item_info = Item(item)
            print(item_info.item_name)
            if not pred_filter(item_info):
                print('Предмет не подходит')
                continue
            have_strick = item_info.check_strick()
            if have_strick:
                profit = get_profit_strick(item_info)
            else:
                profit = get_profit(item_info)
        time.sleep(2)


if __name__ == '__main__':
    csmoney_acc = CSMMarketMethods(None)
    main()
