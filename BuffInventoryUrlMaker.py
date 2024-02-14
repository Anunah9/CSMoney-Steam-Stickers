import urllib.parse
from datetime import datetime
import pprint
from http.cookies import SimpleCookie

import pandas
import requests
import telebot
from bs4 import BeautifulSoup
import sqlite3
from pycbrf import ExchangeRates


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
        'extra_tag_ids': tags
    }
    url = base_url + urllib.parse.urlencode(params).replace('+', '').replace('%5D', '').replace('%5B', '')
    return url


def sticker_to_db(sticker_name, tag):
    query = f'INSERT INTO BuffStickerTags (sticker_name, sticker_tag) VALUES ("{sticker_name}", {tag})'
    cur.execute(query)
    db.commit()


def main():
    items = get_inventory()
    for item in items:
        stickers = item['asset_info']['info']['stickers']
        goods_id = item['goods_id']
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
        bot.send_photo(368333609, img_first_sticker, url)


if __name__ == '__main__':
    raw_cookie = r'Device-Id=aNduRsrfR3TO6DaGEefE; Locale-Supported=en; game=csgo; ' \
                 r'session=1-TItbUB20RKIKUuYuvpib4cVvjrAKe1mlhePKCEAaYNKS2037019629; ' \
                 r'client_id=b2oq15ogSFAJa4ibS5sDOA; display_appids="[730\054 570\054 1]"; ' \
                 r'csrf_token=ImM4MWI5OTkwMTJmZjQzZGI2YTIzNmQ4ZWEzMDQwYzhmZDlhMTIwYzEi.GKoTrA' \
                 r'.hhwdeS8NvqBGG18tAExA6zzQ29w'
    cookie = SimpleCookie()
    cookie.load(raw_cookie)
    BUFF_COOKIE = {k: v.value for k, v in cookie.items()}

    API = '5096520863:AAHHvfFpQTH5fuXHjjAfzYklNGBPw4z57zA'
    bot = telebot.TeleBot(API)
    db = sqlite3.connect('./db/CS.db')
    cur = db.cursor()

    main()
