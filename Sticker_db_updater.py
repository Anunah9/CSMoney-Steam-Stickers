import json
import pprint
import sqlite3
from urllib.parse import unquote
import utils.Utils

import html2json
import requests
from bs4 import BeautifulSoup

def add_to_db(sticker_name, price):
    query = f'INSERT INTO CSMoneyStickerPrices VALUES ("{sticker_name}", {price})'
    cur.execute(query)

def get_all_sticker_prices():
    url = 'https://www.csgo.exchange/prices/'
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'lxml')
    items = soup.find('tbody', class_='contentItems')
    stickers = items.findAll('tr', attrs={'data-type': ' Sticker '})
    print(len(stickers))
    for sticker in stickers:
        sticker_name = unquote(sticker['data-name'])
        price = round(curresncy.change_currency(float(sticker['data-vn'])), 2)
        add_to_db(sticker_name, price)
        # print(sticker_name)
        # print(price)
    

def main():
    print('11')
    get_all_sticker_prices()


if __name__ == '__main__':
    db = sqlite3.connect('db/CS.db')
    cur = db.cursor()
    curresncy = utils.Utils.Currensy()
    main()
    db.commit()
    db.close()
