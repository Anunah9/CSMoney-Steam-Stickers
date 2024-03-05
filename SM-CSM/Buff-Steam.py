# -*- coding: utf-8 -*-
import asyncio
import datetime
import os
import pprint
import sqlite3
import sys
import time
import urllib.parse

import aiohttp
import requests
import telebot
from steampy import models

import Sticker_db_updater

from utils import Utils, resetRouter, BuffAPI

if sys.platform:
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


def get_items_from_db():
    cur = params.cs_db.cursor()
    query = 'SELECT * FROM BuffItemsForTrack'
    return cur.execute(query).fetchall()


def get_sticker_price(sticker_names):
    handled_stickers = []
    for sticker in sticker_names:
        sticker_price1 = get_sticker_prices(sticker)
        sticker['price'] = round(sticker_price1, 2)
        handled_stickers.append(sticker)
    return handled_stickers


def get_sticker_prices(sticker):
    sticker_name = sticker['name']
    price = params.stickers_prices[sticker_name]
    return price


def add_to_checked(item_name, item_id):
    cur = params.cs_db.cursor()
    time_now = datetime.datetime.now().time().strftime("%H:%M:%S")
    query = f'INSERT INTO checkedBuff (item_id, item_name, timestamp) VALUES ("{item_id}", "{item_name}", "{time_now}")'
    cur.execute(query)
    params.cs_db.commit()


def check_handled_items(item_id):
    cur = params.cs_db.cursor()
    query = f'SELECT * FROM checkedBuff WHERE item_id = "{item_id}"'
    check = cur.execute(query).fetchone()
    return bool(check)


def find_strics(lst):
    element_count = {}  # Создаем пустой словарь для хранения количества элементов

    for item in lst:
        name = item['name']
        if name in element_count:
            element_count[name]['count'] += 1
        else:
            element_count[name] = {'count': 1, 'price': item['price']}

    # Фильтруем элементы, оставляем только те, что встречаются 3 и более раз
    filtered_elements = {name: info for name, info in element_count.items() if info['count'] >= 3}

    return filtered_elements


def buy_item(item_name, market_id, price, fee):
    params.steamAccMain.steamclient.market.buy_item(item_name, market_id, price, fee, game=models.GameOptions.CS,
                                                    currency=models.Currency.RUB)


class Item:
    item_name = None
    item_link = None
    goods_id = None
    price_buff = None
    lowest_bargain_price = None
    stickers = None
    listing_id = None
    sticker_tags = None
    sticker_premium = None
    sell_id = None

    def print_item_info(self):
        print(f"Назввние: {self.item_name} \nЦена бафф: {self.price_buff}\n"
              + f"Listing id: {self.listing_id} \nСтикеры: {self.stickers}")


def get_sticker_from_db(sticker_name):
    cur = params.cs_db.cursor()
    query = f'SELECT sticker_tag FROM BuffStickerTags WHERE sticker_name = "{sticker_name}"'
    tag = cur.execute(query).fetchone()
    if not tag:
        return []
    return tag[0]


def sticker_to_db(sticker_name, tag):
    cur = params.cs_db.cursor()
    query = f'INSERT INTO BuffStickerTags (sticker_name, sticker_tag) VALUES ("{sticker_name}", {tag})'
    cur.execute(query)
    params.cs_db.commit()


def get_sticker_tag(sticker_name):
    url = f'https://buff.163.com/api/market/order_tags?page_num=1&game=csgo&page_size=20&use_suggestion=0&category=sticker&search={sticker_name}'
    response = requests.get(url).json()
    sticker = response['data']['items']
    if sticker:
        sticker = sticker[0]
        tag = sticker['id']
        return tag
    else:
        return 0


def get_stickers(item_info):
    stickers = item_info['asset_info']['info']['stickers']
    # pprint.pprint(item_info)
    tags = []
    stickers_result = []
    for sticker in stickers:
        name = sticker['name']
        tag = get_sticker_from_db(name)
        if not tag:
            tag = get_sticker_tag(name)
            if tag == 0:
                continue
            sticker_to_db(name, tag)
        tags.append(tag)

        if sticker['wear'] > 0:
            continue
        stickers_result.append({'slot': sticker['slot'], 'name': 'Sticker | ' + sticker['name']})
    return stickers_result, tags


def create_url(item: Item):
    print(item.tags)
    base_url = f'https://buff.163.com/goods/{item.goods_id}#'
    params = {
        'extra_tag_ids': item.tags
    }
    url = base_url + urllib.parse.urlencode(params).replace('+', '').replace('%5D', '').replace('%5B', '')
    return url


def item_handler(item_obj: Item, counter):
    stickers = get_sticker_price(item_obj.stickers)
    sum_prices_stickers = sum(list(map(lambda x: x['price'], stickers)))
    strick_stickers = find_strics(stickers)
    strick_sticker_name = ''
    strick_count = 0
    strick_price = 0
    sum_price_strick = 0
    if item_obj.sticker_premium and item_obj.sticker_premium > 5:
        return
    print(f'striiiiiiiiiiic: {bool(strick_stickers)}')
    if strick_stickers:
        strick_sticker_name = list(strick_stickers.keys())[0]
        strick_count = strick_stickers[strick_sticker_name]['count']
        strick_price = strick_stickers[strick_sticker_name]['price']
        sum_price_strick = strick_price * strick_count

    print('---------------------------------------------------', strick_sticker_name)
    print(strick_stickers)
    url = create_url(item_obj)

    message = f"{int(len(item_obj.item_name)/2)*'*'}**BUFF163**{int(len(item_obj.item_name)/2)*'*'} \n" \
              f"🌟 **{item_obj.item_name}** 🌟\n" \
              f"Предмет #{counter}\n" \
              f"Ссылка: {url}\n" \
              f"💲 Цена Buff: {round(item_obj.price_buff, 2)} Руб\n" \
              f"Наименьшая цена для торговли: {round(params.currency.change_currency('CNY', 'RUB', item_obj.lowest_bargain_price), 2)}\n"
    if item_obj.sticker_premium:
        message += f"Sticker Premium: {round(item_obj.sticker_premium, 3)*100}%\n"
    else:
        message += f"Sticker Premium: None\n"
    message +=f"🔖 Стикеры:\n" \
              f"💲 Общая стоимость стикеров: {round(sum_prices_stickers, 2)} Руб\n"

    for sticker in stickers:
        message += f"   • {sticker['name']} - 💲 Цена: {sticker['price']} Руб\n" \
            # f"        📈 Переплата min: {sticker['min_overpay']} Руб\n" \
        # f"        📈 Переплата max: {sticker['max_overpay']} Руб\n"
    if strick_stickers:
        message += f"🌟 **Стрики из стикеров** 🌟\n" \
                   f"💲 Общая стоимость стрика: {round(sum_price_strick, 2)} Руб\n" \
                   f"   • {strick_sticker_name} - 💲 Цена: {strick_price} Руб\n" \
                   f"      Количество - {strick_count} \n"
    print(message)
    if sum_prices_stickers > item_obj.price_buff * mult_for_common_item:
        params.bot.send_message(368333609, message)  # Я
        if autobuy:
            params.buffAcc.buy_item(f'https://buff.163.com/goods/{item_obj.goods_id}', item_obj.sell_id)
    if strick_count == 3 and strick_count >= min_stickers_in_strick:
        if sum_price_strick > item_obj.price_buff * mult_for_strick_3 and sum_prices_stickers > min_limit_strick_price:
            params.bot.send_message(368333609, message)  # Я
            if autobuy:
                params.buffAcc.buy_item(f'https://buff.163.com/goods/{item_obj.goods_id}', item_obj.sell_id)
    elif strick_count >= 4:
        if sum_price_strick > item_obj.price_buff * mult_for_strick_4 and sum_prices_stickers > min_limit_strick_price:
            params.bot.send_message(368333609, message)  # Я
            if autobuy:
                params.buffAcc.buy_item(f'https://buff.163.com/goods/{item_obj.goods_id}', item_obj.sell_id)




def items_iterator(item, listings):
    item_obj = Item()
    item_obj.item_name = item[0]
    item_obj.goods_id = item[2]

    counter = 0

    try:
        for listing in listings:
            counter += 1
            item_id = listing['asset_info']['id']

            # print(item[0], item_id)
            listing_splited = listing['id'].split('-')
            sell_id = listing_splited[0]+'-'+listing_splited[1]
            item_obj.sell_id = sell_id
            # print(sell_id)
            # pprint.pprint(listing)
            if check_handled_items(item_id):
                continue
            print(f'listing №{counter}')
            add_to_checked(item_obj.item_name, listing['asset_info']['id'])
            item = listing
            item_obj.listing_id = item['asset_info']['id']
            try:
                item_obj.price_buff = params.currency.change_currency('CNY', "RUB", float(item['price']))
            except KeyError:
                return False
            stickers, tags = get_stickers(item)
            if not stickers:
                continue
            item_obj.stickers = stickers
            item_obj.tags = tags
            item_obj.lowest_bargain_price = float(listing['lowest_bargain_price'])
            if listing['sticker_premium']:
                item_obj.sticker_premium = float(listing['sticker_premium'])

            else:
                item_obj.sticker_premium = None
            print(tags)
            print(stickers)
            item_handler(item_obj, counter)

    except AttributeError:
        print('Ошибка atributeError, listings: ', listings)


def update_csm_prices_in_db(item_name, price):
    query = f'UPDATE items_for_track SET price = {price} WHERE market_hash_name = "{item_name}"'
    params.cs_db.cursor().execute(query)
    params.cs_db.commit()


class Params:
    bot: telebot.TeleBot = None
    cs_db = sqlite3.connect('./db/CS.db')
    t_before_429 = None
    steamAccMain = None
    steamAccServer = None
    buffAcc = BuffAPI.BuffBuyMethods()
    reset_router = resetRouter.ResetRouter()
    currency = Utils.Currensy()
    get_float_error_counter = 0
    stickers_prices = cs_db.cursor().execute('SELECT * FROM CSMoneyStickerPrices').fetchall()
    first_start = True
    counter_requests = 0
    counter_for_too_many_request = 0


    def determination_of_initial_parameters(self):
        self.bot = telebot.TeleBot(API)
        self.bot_error_logger = telebot.TeleBot(API_ErrorLogger)
        self.bot_error_logger.send_message(368333609, 'Запуск бота')  # Я


def read_config(file_path):
    config = {}
    with open(file_path, 'r') as file:
        for line in file:
            key, value = line.strip().split('=')
            config[key] = value
    return config


def restart_program():
    python = sys.executable
    os.execl(python, python, *sys.argv)


async def fetch_data(session, item, counter, count_items):
    item_name = item[0]
    url = f'https://buff.163.com/api/market/goods/sell_order?game=csgo&goods_id={item[2]}&page_num=1&sort_by=default&mode=&allow_tradable_cooldown=1&_=1707927946965'

    delay = 0.85 * counter
    await asyncio.sleep(delay)
    try:
        t1 = time.time()
        response = await session.get(url)
        # print('Время одного запроса: ', time.time() - t1)
        params.counter_requests += 1
        if response.status == 200:
            params.counter_for_too_many_request = 0
            data = await response.json()
            listings = data
            if 'data' in listings:
                listings = listings['data']['items']
                items_iterator(item, listings)


    except aiohttp.ClientError as e:
        print(f'Error during request to {url}: {e}')

    except asyncio.exceptions.TimeoutError:
        print('Timeout Error')


async def main():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/120.0.0.0 YaBrowser/24.1.0.0 Safari/537.36',
        "Referer": "https://buff.163.com/"
    }
    session = aiohttp.ClientSession(headers=headers, cookies={'Locale-Supported': 'en'})
    start = 0
    while True:
        items = get_items_from_db()
        print('Количество предметов: ', len(items))
        for item in items:
            print(item[0])
        try:
            print('---------------------------------------')

            tasks1 = []
            counter = 0
            iter_time = round(60 / len(items))
            print('Кол-во секунд на полную итерацию', iter_time)

            for i in range(iter_time):
                for item in items:
                    tasks1.append(fetch_data(session, item, counter, len(items)))
                    counter += 1
            t2 = time.time()
            await asyncio.gather(*tasks1)
            result_time = time.time() - t2
            target_delay = 60 - result_time
            print('Время выполенения запросов: ', result_time)
            print('Задержка до нужного времени: ', target_delay)
            print('Количество выполненных запросов: ', counter)
            t3 = time.time()
            # await asyncio.sleep(target_delay if target_delay > 0 else 0)
            print('Проверка задержки: ', time.time() - t3)
        except AttributeError:
            params.bot_error_logger.send_message(368333609, 'Ошибка Attribute error')  # Я
            Utils.close_server()
            params.bot_error_logger.send_message(368333609, 'Перезагружаю роутер')  # Я
            params.reset_router.reset_router()
            restart_program()

        except Exception as exc:
            try:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print(exc_type, fname, exc_tb.tb_lineno)
                params.bot_error_logger.send_message(368333609,
                                        'Ошибка в основном цикле: ' + f'{str(exc)}, {exc_type}, {fname}, {exc_tb.tb_lineno}')  # Я
            except Exception as exc1:
                print(exc1)
            print(exc)

if __name__ == '__main__':

    API = '5096520863:AAHHvfFpQTH5fuXHjjAfzYklNGBPw4z57zA'
    API_ErrorLogger = '6713247775:AAEq_pT350E8rUuyaz8eSWvyMYawK1Iqz9c'
    params = Params()
    params.determination_of_initial_parameters()
    params.convert_stickers_to_dict()
    # print(params.stickers_prices)
    config = read_config('configBuff.txt')

    mult_for_strick_3 = float(config.get('MULT_FOR_STRICK_3'))
    mult_for_strick_4 = float(config.get('MULT_FOR_STRICK_4'))
    min_stickers_in_strick = int(config.get('MIN_STICKERS_IN_STRICK'))
    mult_for_common_item = float(config.get('MULT_FOR_COMMON_ITEM'))

    test_params = False
    if test_params:
        autobuy = False
    else:
        autobuy = config.get('AUTOBUY')

    min_limit_strick_price = int(config.get('MIN_LIMIT_PRICE_FOR_STRICK'))
    setting_message = f"**Текущие настройки бота** \n" \
                      f"Текущий баланс💲: {0} Руб\n" \
                      f"Коэффициенты для стоимости стрика: {mult_for_strick_3}\n" \
                      f"Коэффициенты для стоимости без стрика: {mult_for_common_item}\n" \
                      f"Автопокупка: {autobuy}\n"

    params.bot_error_logger.send_message(368333609, setting_message)  # Я
    params.t_before_429 = time.time()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
