import json
import pprint
import sqlite3
from urllib.parse import unquote
import utils.Utils

import html2json
import requests
from bs4 import BeautifulSoup


def add_to_db(sticker_name, price, cur):
    sticker_name = sticker_name.replace('&#39', "'")
    query = f'INSERT INTO CSMoneyStickerPrices VALUES ("{sticker_name}", {price})'
    cur.execute(query)


def get_all_sticker_prices(cur):
    url = 'https://www.csgo.exchange/prices/'
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'lxml')
    items = soup.find('tbody', class_='contentItems')
    stickers = items.findAll('tr', attrs={'data-type': ' Sticker '})
    print(len(stickers))
    for sticker in stickers:
        sticker_name = unquote(sticker['data-name'])
        price = float(sticker['data-vn'])
        add_to_db(sticker_name, price, cur)
        # print(sticker_name)
        # print(price)


def get_all_sticker_prices_v2(cur):
    url = 'http://csgobackpack.net/api/GetItemsList/v2/'
    response = requests.get(url).json()
    items = response["items_list"]
    stickers = list(filter(lambda x: "Sticker |" in x, items.keys()))

    for sticker in stickers:
        item = items[sticker]
        # print(sticker)
        # pprint.pprint(item)
        if 'price' in item:
            try:
                median_price = item['price']['7_days']['median']
            except:
                median_price = item['price']['all_time']['median']
        else:
            median_price = 0
        add_to_db(sticker, median_price, cur)


def main():
    db = sqlite3.connect('db/CS.db')
    cur = db.cursor()
    print('11')
    get_all_sticker_prices_v2(cur)
    db.commit()
    db.close()
    print('Цены обновлены.')


if __name__ == '__main__':

    main()

