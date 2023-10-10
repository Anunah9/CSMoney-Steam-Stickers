import asyncio
import os
import signal
import sqlite3
import subprocess
import sys
import time

import bs4
import requests
from steampy import models, exceptions
import telebot

import utils.CSMoneyAPI
from utils import SteamMarketAPI, Utils, resetRouter
from subprocess import call

"""Модуль отслеживания предметов:
-Взять предметы из бд
-Пройтись по каждому и выполнить следующее:
    -Узнать цену предмета
    -Узнать какие наклейки есть, их потертость и их цену
    -Если цены на наклейки приемлимые и наклейки не стертые то
        -Посмотреть переплату за эти наклейки на кс мани (сложный пункт с ним будем разбираться в модуле по работе 
        с площадками)
        -Если переплата больше чем минимальный процент профита
        -Купить предмет"""

if sys.platform:
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


def get_items_from_db():
    cur = params.cs_db.cursor()
    query = 'SELECT * FROM items_for_track'
    return cur.execute(query).fetchall()


def get_item_listings(market_hash_name):
    listings = params.steamAcc.get_item_listigs_only_first_10(market_hash_name)
    # check_test = params.cs_db.cursor().execute('SELECT check_test FROM check_test').fetchone()[0]
    # params.cs_db.cursor().execute('UPDATE check_test SET check_test=1')
    # print('Проверка?: ', check_test)
    # if check_test == 'true':
    #     print('Проверка')
    #     listings = 429

    if listings == 429:
        params.bot.send_message(368333609, 'Ошибка 429')  # Я
        close_server()
        params.bot.send_message(368333609, 'Перезагружаю роутер')  # Я
        params.reset_router.reset_router()
        restart_program()
    else:
        return listings


def get_price_sm(itemnameid_):
    buy_price, _, _, _ = params.steamAcc.get_steam_prices(itemnameid_)
    return buy_price


def get_item_float_and_stickers(inspect_link):
    print('Количество ошибок: ', params.get_float_error_counter)
    url = 'http://192.168.0.14/'
    params_ = {
        'url': inspect_link
    }
    try:
        response = requests.get(url, params=params_)
    except requests.exceptions.ConnectionError:
        close_server()
        start_cs_inspect_server()
        response = requests.get(url, params=params_)
    if response.status_code != 200:
        print('Get float and stickers:', response)
        for test in range(10):
            response = requests.get(url, params=params_)
            print('Test inspect сервера: ', test)
            if response.status_code != 200:
                params.get_float_error_counter += 1
            time.sleep(0.5)
    elif response.status_code == 200:
        params.get_float_error_counter = 0
    if params.get_float_error_counter > 7:
        close_server()
        start_cs_inspect_server()
        response = requests.get(url, params=params_)
        if response.status_code != 200:
            params.reset_router.reset_router()
            restart_program()
        params.get_float_error_counter = 0




    response = response.json()
    # print(response)
    iteminfo = response['iteminfo']
    float_item = iteminfo['floatvalue']
    stickers = iteminfo['stickers']
    stickers_result = []
    for sticker in stickers:
        if 'wear' in sticker:
            continue
        stickers_result.append({'slot': sticker['slot'], 'name': 'Sticker | ' + sticker['name']})

    return float_item, stickers_result


def add_sticker_price_to_db(sticker_name, price):
    pass


def get_desired_stickers_from_item(item, sticker_name):
    stickers = item['stickers']
    sticker_name = sticker_name['name']
    desired_stickers = []
    for sticker in stickers:
        if not sticker:
            continue
        if sticker['name'] == sticker_name:
            desired_stickers.append(sticker)
    return desired_stickers


def min_max_overpay(sticker):
    min_overpay = min(sticker['overpays'], key=lambda x: x['overpay'])['overpay']
    max_overpay = max(sticker['overpays'], key=lambda x: x['overpay'])['overpay']
    return min_overpay, max_overpay


def get_sticker_price(sticker_names):
    handled_stickers = []
    for sticker in sticker_names:
        sticker_price1 = get_sticker_prices(sticker)
        sticker['price'] = round(sticker_price1, 2)
        handled_stickers.append(sticker)
    return handled_stickers


def get_sticker_prices(sticker):
    sticker_name = sticker['name']
    price = params.stickers_prices[sticker_name.lower()]
    return price


def add_to_checked(item_name, item_id):
    cur = params.cs_db.cursor()
    query = f'INSERT INTO checked (item_id, item_name) VALUES ({item_id}, "{item_name}")'
    cur.execute(query)
    params.cs_db.commit()


def check_handled_items(item_id):
    cur = params.cs_db.cursor()
    query = f'SELECT * FROM checked WHERE item_id = {item_id}'
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
    params.steamAcc.steamclient.market.buy_item(item_name, market_id, price, fee, game=models.GameOptions.CS,
                                                currency=models.Currency.RUB)


class Item:
    item_name = None
    item_link = None
    price_sm = None
    stickers = None
    listing_id = None
    price_no_fee = None
    fee = None


def item_handler(item_obj: Item, counter):
    stickers = get_sticker_price(item_obj.stickers)
    sum_prices_stickers = sum(list(map(lambda x: x['price'], stickers)))
    strick_stickers = find_strics(stickers)
    strick_sticker_name = ''
    strick_count = 0
    strick_price = 0
    sum_price_strick = 0
    print(f'striiiiiiiiiiic: {bool(strick_stickers)}')
    if strick_stickers:
        strick_sticker_name = list(strick_stickers.keys())[0]
        strick_count = strick_stickers[strick_sticker_name]['count']
        strick_price = strick_stickers[strick_sticker_name]['price']
        sum_price_strick = strick_price * strick_count

    print('---------------------------------------------------', strick_sticker_name)
    print(strick_stickers)
    message = f"🌟 **{item_obj.item_name}** 🌟\n" \
              f"Предмет #{counter}\n" \
              f"Ссылка: {item_obj.item_link}\n" \
              f"💲 Цена SM: {item_obj.price_sm} Руб\n" \
              f"🔖 Стикеры:\n" \
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
    if sum_prices_stickers > item_obj.price_sm * mult_for_common_item:
        if autobuy:
            buy_item(item_obj.item_name, item_obj.listing_id, item_obj.price_no_fee + item_obj.fee, item_obj.fee)
        params.bot.send_message(368333609, message)  # Я
    if strick_count == 3:
        if sum_price_strick > item_obj.price_sm * mult_for_strick_3 and sum_prices_stickers > min_limit_strick_price:
            if autobuy:
                buy_item(item_obj.item_name, item_obj.listing_id, item_obj.price_no_fee + item_obj.fee, item_obj.fee)
            params.bot.send_message(368333609, message)  # Я
    elif strick_count == 4:
        if sum_price_strick > item_obj.price_sm * mult_for_strick_4 and sum_prices_stickers > min_limit_strick_price:
            if autobuy:
                buy_item(item_obj.item_name, item_obj.listing_id, item_obj.price_no_fee + item_obj.fee, item_obj.fee)
        # Улучшенный вариант сообщения
            params.bot.send_message(368333609, message)  # Я


def items_iterator(item_name, item_link, listings):
    item_obj = Item()
    item_obj.item_name = item_name
    item_obj.item_link = item_link
    counter = 0

    try:
        for key in listings.keys():
            counter += 1
            if check_handled_items(key):
                # print(check_handled_items(key))
                continue
            print(f'listing №{counter}')
            add_to_checked(item_name, key)
            item = listings[key]
            item_obj.listing_id = item['listingid']
            try:
                item_obj.price_no_fee = item['converted_price']

                item_obj.fee = item['converted_fee']
                price_sm = (item_obj.price_no_fee + item_obj.fee) / 100
                item_obj.price_sm = price_sm

                inspect_link = item['asset']['market_actions'][0]['link'].replace('%listingid%', key).replace(
                    '%assetid%',
                    item['asset']['id'])
            except KeyError:
                return False
            # link = {'link': inspect_link}
            try:
                float_item, stickers = get_item_float_and_stickers(inspect_link)
            except KeyError as exc2:
                float_item, stickers = 2, []
                print(f'Get Float Failed: {exc2}')
            if not stickers:
                continue
            item_obj.stickers = stickers

            print(stickers)
            if test_params:
                print('Тестовый запрос')
                test_item = Item()
                test_item.item_name = 'AK-47 | Elite Build (Minimal Wear)'
                test_item.item_link = 'https://steamcommunity.com/market/listings/730/AK-47%20%7C%20Elite%20Build%20(Minimal%20Wear)'
                inspect_link = 'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20S76561198187797831A33359047868D14152186399717878141'
                float_item, stickers = get_item_float_and_stickers(inspect_link)
                print('Тесстт', stickers)

                test_item.price_sm = 212.31
                test_item.stickers = stickers
                test_item.listing_id = 12314515243543
                test_item.price_no_fee = 212
                test_item.fee = 10
                item_handler(test_item, counter)
            else:
                item_handler(item_obj, counter)

    except AttributeError:
        print('Ошибка atributeError, listings: ', listings)


def update_csm_prices_in_db(item_name, price):
    query = f'UPDATE items_for_track SET price = {price} WHERE market_hash_name = "{item_name}"'
    params.cs_db.cursor().execute(query)
    params.cs_db.commit()


def try_login():
    while True:
        try:
            steamAcc = SteamMarketAPI.SteamMarketMethods()
            params.bot.send_message(368333609, 'Создание экземпляра steamAcc успешно')  # Я
            return steamAcc
        except ConnectionError:
            params.bot.send_message(368333609, 'Ошибка Connection error, пробую снова')  # Я
            time.sleep(5)
        except exceptions.CaptchaRequired:
            params.bot.send_message(368333609, 'Ошибка Captcha required, перезагружаю роутер')  # Я
            params.reset_router.reset_router()
            restart_program()
        except Exception as exc2:
            params.bot.send_message(368333609, f'Ошибка try login: {exc2}')
            params.reset_router.reset_router()
            restart_program()


class Params:
    bot: telebot.TeleBot = None
    cs_db = sqlite3.connect('./db/CS.db')
    steamAcc = None
    csm_acc = utils.CSMoneyAPI.CSMMarketMethods(None)
    reset_router = resetRouter.ResetRouter()
    currency = Utils.Currensy()
    get_float_error_counter = 0
    stickers_prices = cs_db.cursor().execute('SELECT * FROM CSMoneyStickerPrices').fetchall()
    first_start = True

    def convert_stickers_to_dict(self):
        sticker_prices_dict = {}
        for sticker in self.stickers_prices:
            sticker_prices_dict[sticker[0]] = sticker[1]
        self.stickers_prices = sticker_prices_dict

    def determination_of_initial_parameters(self):
        self.bot = telebot.TeleBot(API)
        self.bot.send_message(368333609, 'Запуск бота')  # Я
        self.steamAcc = try_login()
        self.bot.send_message(368333609,
                              f'Авторизация в стиме: {params.steamAcc.steamclient.is_session_alive()}')  # Я
        print(params.steamAcc.steamclient.is_session_alive())
        self.bot.send_message(368333609, 'Запуск inspect сервера')  # Я
        close_server()
        start_cs_inspect_server()


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


def get_pid_server():
    with open(r'C:\Users\Sasha\Desktop\CSGOFloatInspect\node_pid.txt') as f:
        pid = f.read()
        return pid


def close_server():
    pid = get_pid_server()
    print(f'PID запущенного процесса: {pid}')
    print('Выключаю сервер...')
    subprocess.run(['taskkill', '/F', '/T', '/PID', str(pid)], shell=True)


def start_cs_inspect_server():
    server_path = r'C:\Users\Sasha\Desktop\CSGOFloatInspect'
    indexjs_path = os.path.join(server_path, 'index.js')
    print('Запускаю сервер...')
    try:
        p1 = subprocess.Popen(['start', 'cmd', '/k', 'cd', server_path, '^&', 'node', indexjs_path], shell=True)
        time.sleep(15)
    except Exception as e:
        print(f'Произошла ошибка при запуске сервера: {str(e)}')


def main():
    start = 0
    counter = start + 1
    items = get_items_from_db()
    # print(items)
    t1 = time.time()
    # balance = params.steamAcc.steamclient.get_wallet_balance()

    for item in items[start::]:
        item_name, link, _, _, _ = item
        # print('Баланс кошелька: ', balance)

        if params.first_start:
            price_csm = params.csm_acc.get_price(item_name)
            print('Цена ксм: ', price_csm)
            update_csm_prices_in_db(item_name, price_csm)
        t3 = time.time()
        try:
            listings = get_item_listings(item_name)
        except requests.exceptions.ReadTimeout:
            print('TimeoutError')
            continue
        print('Get listings: ', time.time() - t3)
        # print(listings)
        print('-------------------------------------------------------------')
        print(f"Предмет {counter} из {len(items)}")
        print(item_name)
        counter += 1
        if listings == 429:
            break
        if not (items_iterator(item_name, link, listings)):
            continue
    params.first_start = False
    print(time.time() - t1)


if __name__ == '__main__':
    API = '5096520863:AAHHvfFpQTH5fuXHjjAfzYklNGBPw4z57zA'
    params = Params()
    params.determination_of_initial_parameters()
    params.convert_stickers_to_dict()
    # print(params.stickers_prices)
    config = read_config('./config.txt')

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

    params.bot.send_message(368333609, setting_message)  # Я

    while True:
        try:
            if main() == 'low balance':
                print('low balance')
                break
        except AttributeError:
            params.bot.send_message(368333609, 'Ошибка Attribute error')  # Я
            close_server()
            params.bot.send_message(368333609, 'Перезагружаю роутер')  # Я
            params.reset_router.reset_router()
            restart_program()

        except Exception as exc:
            try:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print(exc_type, fname, exc_tb.tb_lineno)
                params.bot.send_message(368333609, 'Ошибка в основном цикле: '+ f'{str(exc)}, {exc_type}, {fname}, {exc_tb.tb_lineno}')  # Я
            except Exception as exc1:

                print(exc1)
            print(exc)
