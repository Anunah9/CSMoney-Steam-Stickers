import os
import signal
import sqlite3
import subprocess
import sys
import time
import requests
from steampy import models, exceptions
import telebot
from utils import CSMoneyAPI, SteamMarketAPI, Utils, resetRouter
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
        params.get_float_error_counter += 1
    elif response.status_code == 200:
        params.get_float_error_counter = 0
    if params.get_float_error_counter > 10:
        close_server()
        start_cs_inspect_server()
        response = requests.get(url, params=params_)


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


def get_price_csm(market_hash_name):
    return params.csmoney_acc.get_price(market_hash_name)


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


def filter_stickers(items_from_csm, sticker_name):
    desired_sticker = []
    for item in items_from_csm:
        desired_sticker += get_desired_stickers_from_item(item, sticker_name)
    return desired_sticker


def min_max_overpay(sticker):
    min_overpay = min(sticker['overpays'], key=lambda x: x['overpay'])['overpay']
    max_overpay = max(sticker['overpays'], key=lambda x: x['overpay'])['overpay']
    return min_overpay, max_overpay


def get_sticker_overpay(item_name, sticker_names, csm_price):
    print(sticker_names)
    handled_stickers = []
    for sticker in sticker_names:
        items = params.csmoney_acc.get_sticker_overpay(item_name, sticker, csm_price=csm_price)
        if 'error' in items:
            continue
        items = items['items']
        desired_stickers = filter_stickers(items, sticker)  # Инфа о скинах с этой наклейкой найденые на cs money
        sticker_price = params.currency.change_currency(desired_stickers[0]['price'])
        overpays = []
        for sticker_ in desired_stickers:
            if sticker_['overprice']:
                overprice = float(sticker_['overprice'])

            else:
                overprice = 0
            overpays.append(overprice)
        overpay_min = min(overpays)
        overpay_max = max(overpays)
        sticker['price'] = round(sticker_price, 2)
        sticker['min_overpay'] = round(params.currency.change_currency(overpay_min))
        sticker['max_overpay'] = round(params.currency.change_currency(overpay_max))
        handled_stickers.append(sticker)

    return handled_stickers


def get_profit(csm_price, sm_price, min_overpay, max_overpay):
    min_price_csm = csm_price + min_overpay
    max_price_csm = csm_price + max_overpay
    profit_min_item = round((min_price_csm / sm_price - 1) * 100, 2)
    profit_max_item = round((max_price_csm / sm_price) * 100, 2)
    profit_min_sticker = round((min_overpay / sm_price) * 100, 2)
    profit_max_sticker = round((max_overpay / sm_price) * 100, 2)
    return profit_min_sticker, profit_max_sticker


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


def handle_listings(item_name, item_link, listings):
    links = []
    price_csm = get_price_csm(item_name) * 0.95
    counter = 0
    if not price_csm:
        return False
    try:
        for key in listings.keys():
            counter += 1
            print(f'listing №{counter}')
            if check_handled_items(key):
                print(check_handled_items(key))
                continue
            add_to_checked(item_name, key)
            item = listings[key]
            try:
                price_no_fee = item['converted_price']
                fee = item['converted_fee']
                price_sm = (price_no_fee + fee) / 100
                inspect_link = item['asset']['market_actions'][0]['link'].replace('%listingid%', key).replace(
                    '%assetid%',
                    item['asset']['id'])
            except KeyError:
                return False
            link = {'link': inspect_link}
            links.append(link)
            try:
                float_item, stickers = get_item_float_and_stickers(inspect_link)
            except KeyError:

                float_item, stickers = 2, []

                print('Get Float Failed')
            if not stickers:
                continue
            stickers = get_sticker_overpay(item_name, stickers, price_csm)
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
            min_overpay_all_stickers = sum(list(map(lambda x: x['min_overpay'], stickers)))
            max_overpay_all_stickers = sum(list(map(lambda x: x['max_overpay'], stickers)))
            profit_min, profit_max = get_profit(price_csm, price_sm, min_overpay_all_stickers, max_overpay_all_stickers)

            if (profit_min >= min_limit_profit and sum_prices_stickers > price_sm * mult_for_common_item) \
                    or (sum_price_strick > price_sm * mult_for_strick and sum_prices_stickers > min_limit_strick_price
                        and strick_count < min_stickers_in_strick):
                listing_id = item['listingid']
                if autobuy:
                    buy_item(item_name, listing_id, price_no_fee + fee, fee)
                # Улучшенный вариант сообщения
                message = f"🌟 **{item_name}** 🌟\n" \
                          f"Предмет #{counter}\n" \
                          f"Ссылка: {item_link}\n" \
                          f"💲 Цена SM: {price_sm} Руб\n" \
                          f"💲 Цена CSM: {round(price_csm, 2)} Руб\n" \
                          f"🔖 Стикеры:\n" \
                          f"💲 Общая стоимость стикеров: {round(sum_prices_stickers, 2)} Руб\n"
                for sticker in stickers:
                    message += f"   • {sticker['name']} - 💲 Цена: {sticker['price']} Руб\n" \
                               f"        📈 Переплата min: {sticker['min_overpay']} Руб\n" \
                               f"        📈 Переплата max: {sticker['max_overpay']} Руб\n"
                if strick_stickers:
                    message += f"🌟 **Стрики из стикеров** 🌟\n" \
                               f"💲 Общая стоимость стрика: {round(sum_price_strick, 2)} Руб\n" \
                               f"   • {strick_sticker_name} - 💲 Цена: {strick_price} Руб\n" \
                               f"      Количество - {strick_count} \n"
                message += f"📈 Переплата за все стикеры min: {round(min_overpay_all_stickers, 2)} Руб\n" \
                           f"📈 Переплата за все стикеры max: {round(max_overpay_all_stickers, 2)} Руб\n" \
                           f"🚀 Профит min: {profit_min}%\n"
                print(message)
                params.bot.send_message(368333609, message)  # Я
    except AttributeError:
        print('Ошибка atributeError, listings: ', listings)


def main():
    start = 0
    counter = start
    items = get_items_from_db()

    print(items)
    t1 = time.time()
    for item in items[start::]:
        balance = params.steamAcc.steamclient.get_wallet_balance()
        print('Баланс кошелька: ', balance)
        if balance < limit_balance:
            return 'low balance'
        item_name, link, _, _, _ = item
        print('-------------------------------------------------------------')
        print(f"Предмет {counter} из {len(items)}")
        counter += 1
        listings = get_item_listings(item_name)
        if listings == 429:
            break
        if not (handle_listings(item_name, link, listings)):
            continue
    print(time.time() - t1)


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
            print('Ожидайте...')
            time.sleep(120)


class Params:
    bot: telebot.TeleBot = None
    cs_db = sqlite3.connect('./db/CS.db')
    steamAcc = None
    csmoney_acc = CSMoneyAPI.CSMMarketMethods(None)
    reset_router = resetRouter.ResetRouter()
    currency = Utils.Currensy()
    get_float_error_counter = 0

    def determination_of_initial_parameters(self):
        self.bot = telebot.TeleBot(API)
        self.bot.send_message(368333609, 'Запуск бота')  # Я
        self.steamAcc = try_login()
        self.bot.send_message(368333609,
                              f'Авторизация в стиме: {params.steamAcc.steamclient.is_session_alive()}')  # Я
        print(params.steamAcc.steamclient.is_session_alive())
        self.bot.send_message(368333609, 'Запуск inspect сервера')  # Я
        time.sleep(10)
        close_server()
        start_cs_inspect_server()
    # def test_services(self):


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


if __name__ == '__main__':
    API = '5096520863:AAHHvfFpQTH5fuXHjjAfzYklNGBPw4z57zA'
    params = Params()
    params.determination_of_initial_parameters()

    config = read_config('./config.txt')

    mult_for_strick = int(config.get('MULT_FOR_STRICK'))
    min_stickers_in_strick = int(config.get('MIN_STICKERS_IN_STRICK'))
    mult_for_common_item = int(config.get('MULT_FOR_COMMON_ITEM'))

    min_limit_strick_price = int(config.get('MIN_LIMIT_PRICE_FOR_STRICK'))
    min_limit_profit = 10
    limit_balance = 0
    autobuy = config.get('AUTOBUY')
    setting_message = f"**Текущие настройки бота** \n" \
                      f"Текущий баланс💲: {params.steamAcc.steamclient.get_wallet_balance()} Руб\n" \
                      f"Коэффициенты для стоимости стрика: {mult_for_strick}\n" \
                      f"Коэффициенты для стоимости без стрика: {mult_for_common_item}\n" \
                      f"Ограничение по балансу: {limit_balance} Руб\n" \
                      f"Автопокупка: {autobuy}\n"

    params.bot.send_message(368333609, setting_message)  # Я

    while True:
        try:
            if main() == 'low balance':
                print('low balance')
                break
        except Exception as exc:
            try:
                params.bot.send_message(368333609, str(exc))  # Я
            except Exception as exc1:
                print(exc1)
            print(exc)
