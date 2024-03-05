import pickle
import string
import time
import urllib.parse
from datetime import datetime
import pprint
from http.cookies import SimpleCookie
import selenium.webdriver
import pandas
import requests
import telebot
from bs4 import BeautifulSoup
import sqlite3
from pycbrf import ExchangeRates
from selenium.webdriver.common.by import By

from utils import BuffAPI


def get_inventory() -> list:
    url = "https://buff.163.com/api/market/steam_inventory?game=csgo&force=0&page_num=1&page_size=50&search=slate&state=cansell&_=1707643390388"
    response = requests.get(url, cookies=BUFF_COOKIE)
    items = response.json()['data']['items']
    return items


def get_sticker_tag(sticker_name):
    url = f'https://buff.163.com/api/market/order_tags?page_num=1&game=csgo&page_size=20&use_suggestion=0&category=sticker&search={sticker_name}'
    response = requests.get(url).json()
    sticker = response['data']['items'][0]
    tag = sticker['id']
    return tag


def get_sticker_from_db(sticker_name):
    query = f'SELECT sticker_tag FROM BuffStickerTags WHERE sticker_name = "{sticker_name}"'
    tag = cur.execute(query).fetchone()
    if not tag:
        return []
    return tag[0]


def create_url(goods_id, tags):
    base_url = f'https://buff.163.com/goods/{goods_id}#'
    params = {
        'extra_tag_ids': tags,
        'wearless_sticker': 1
    }
    url = base_url + urllib.parse.urlencode(params).replace('+', '').replace('%5D', '').replace('%5B', '')
    return url


def sticker_to_db(sticker_name, tag):
    query = f'INSERT INTO BuffStickerTags (sticker_name, sticker_tag) VALUES ("{sticker_name}", {tag})'
    cur.execute(query)
    db.commit()


def get_prices_with_overpay(goods_id, tags ):
    base_url = f'https://buff.163.com/api/market/goods/sell_order?'

    params = {
        'goods_id': goods_id,
        'game': 'csgo',
        'extra_tag_ids': tags
    }
    url = base_url + urllib.parse.urlencode(params).replace('+', '').replace('%5D', '').replace('%5B', '')
    print(url)
    response = requests.get(url, cookies=BUFF_COOKIE)
    print(response)
    while response.status_code == 429:
        response = requests.get(url, cookies=BUFF_COOKIE)
        print(response)
        time.sleep(2)

    response = response.json()
    items = response['data']['items']
    print(items)
    for item in items:
        sp = item["sticker_premium"]
        if sp is not None:
            sp = float(sp) * 100
            print(sp)
            if sp > 12:
                price = item['price']
                return price, sp
    return 0, 0


def main():
    items = get_inventory()
    buffAcc.open_inventory_page()
    for item in items:
        stickers = item['asset_info']['info']['stickers']
        goods_id = item['goods_id']
        item_id = item['assetid']
        tags = []
        for sticker in stickers:
            name = sticker['name']
            tag = get_sticker_from_db(name)
            if not tag:
                tag = get_sticker_tag(name)
                sticker_to_db(name, tag)
            tags.append(tag)
        img_first_sticker = stickers[0]['img_url']
        url = create_url(goods_id, tags)
        price, sp = get_prices_with_overpay(goods_id, tags)
        if price:
            buffAcc.sell_item_from_inventory(item_id, price)
        message = f"Ссылка: {url}\n" \
                  f"💲 Цена SM: {price} Руб\n" \
                  f"💲 SP: {sp} %\n"

        bot.send_photo(368333609, img_first_sticker, message)


if __name__ == '__main__':
    raw_cookie = r'Device-Id=aNduRsrfR3TO6DaGEefE; Locale-Supported=ru; game=csgo; ' \
                 r'session=1-5kuul3aIeab6uuLOA8b9gg6imnIEpbINaH5C0GCfcXNB2037019629; ' \
                 r'csrf_token=ImFiZjYwN2FjNzg1Njc5ZDYxOWU3ZmQwMzM3NWYwNGZlZjczMzE3ODIi.GMJlmQ' \
                 r'.lfAaRveQORcNlyl1zSqDFYJtUcc'
    cookie = SimpleCookie()
    cookie.load(raw_cookie)
    # BUFF_COOKIE = {k: v.value for k, v in cookie.items()}
    BUFF_COOKIE = {
            "client_id": "65LVFceth3qkcBJaOYibvA",
            "csrf_token": "IjczZDJkNmY0MDhiODYyMzBiOTU5YTZiMGVhODUwYWY0ZTdkY2U1YzUi.GMJqXg.KxBA5nQF7p0Eo1AsY_Cu1VHyAhM",
            "Device-Id": "tPDBlwqlk2ciHMgLZ7cu",
            "display_appids": "\"[730\\054 570\\054 1]\"",
            "game": "csgo",
            "Locale-Supported": "ru",
            "session": "1-UuiIijzXoNMMmShaTHK4MEL8xXx5tQFHGyamSYp7MzaC2037019629"
        }


    print(BUFF_COOKIE)
    buffAcc = BuffAPI.BuffBuyMethods()
    API = '5096520863:AAHHvfFpQTH5fuXHjjAfzYklNGBPw4z57zA'
    bot = telebot.TeleBot(API)
    db = sqlite3.connect('./db/CS.db')
    cur = db.cursor()
    main()
