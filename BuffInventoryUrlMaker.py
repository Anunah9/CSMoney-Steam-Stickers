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


def get_prices_with_overpay(goods_id, tags ):
    base_url = f'https://buff.163.com/api/market/goods/sell_order?'

    params = {
        'goods_id': goods_id,
        'game': 'csgo',
        'extra_tag_ids': tags
    }
    url = base_url + urllib.parse.urlencode(params).replace('+', '').replace('%5D', '').replace('%5B', '')
    print(url)
    response = requests.get(url, cookies=BUFF_COOKIE).json()

    items = response['data']['items']
    print(items)
    for item in items:
        sp = item["sticker_premium"]
        if sp is not None:
            sp = float(sp) * 100
            print(sp)
            if sp > 5:
                price = item['price']
                return price, sp
    return 0, 0


class BuffBuyMethods:
    def __init__(self):
        self.chrome_options = selenium.webdriver.ChromeOptions()
        self.useragent = f'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) ' \
                         f'Chrome/114.0.0.0 YaBrowser/23.7.3.824 Yowser/2.5 Safari/537.36'
        self.chrome_options.add_argument(self.useragent)  # Исправление: Добавить self.useragent
        self.driver = selenium.webdriver.Chrome(options=self.chrome_options)  # Исправление: Передать параметр options
        self.driver.get('https://buff.163.com/market/')
        self.load_cookies()
        self.create_cookie()

        self.already_buy = None
        self.balance = None
        time.sleep(3)

    def create_cookie(self):
        self.driver.execute_script('loginModule.steamLogin()')
        print('жду выполнение логина')
        login = str.lower(input('Вы выполнили авторизацию?(y/n): '))
        if login == 'y':
            print('Сохраняю cookie')
            pickle.dump(self.driver.get_cookies(), open('cookies', 'wb'))
            print('Готово')

    def buy_first_item(self, url):
        self.driver.get(url)
        time.sleep(3)
        self.driver.find_element(By.XPATH, '//*[starts-with(@id, "sell_order_")]/td[6]/a').click()
        time.sleep(3)
        self.driver.find_element(By.XPATH, '//*[@id="j_popup_epay"]/div[2]/div[4]/a').click()

    def load_cookies(self):
        for cookie in pickle.load(open("cookies", "rb")):
            self.driver.add_cookie(cookie)
        self.driver.refresh()
        time.sleep(3)


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
        price, sp = get_prices_with_overpay(goods_id, tags)
        message = f"Ссылка: {url}\n" \
                  f"💲 Цена SM: {price} Руб\n" \
                  f"💲 SP: {sp} %\n"

        bot.send_photo(368333609, img_first_sticker, message)


if __name__ == '__main__':
    raw_cookie = r'Device-Id=aNduRsrfR3TO6DaGEefE; Locale-Supported=ru; game=csgo; ' \
                 r'session=1-KyrQrohAKAdKA4zeMUrJpeJawdrfjmutweIWxyXRIVRL2037019629; ' \
                 r'csrf_token=Ijc5ZTFlZWJiNjA2MzUzOTgzOTMyNGQyZDg0NTc3MzcxNjk1MzlhYTki.GLeKOQ' \
                 r'.lPdj7o_ryrZC3VO3bfDhMXRkTik'
    cookie = SimpleCookie()
    cookie.load(raw_cookie)
    BUFF_COOKIE = {k: v.value for k, v in cookie.items()}
    print(BUFF_COOKIE)
    API = '5096520863:AAHHvfFpQTH5fuXHjjAfzYklNGBPw4z57zA'
    bot = telebot.TeleBot(API)
    db = sqlite3.connect('./db/CS.db')
    cur = db.cursor()
    buffAcc = BuffBuyMethods()



    main()
