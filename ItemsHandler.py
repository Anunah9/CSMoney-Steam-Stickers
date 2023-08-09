import sqlite3
import time
import requests
import telebot
from utils import CSMoneyAPI, SteamMarketAPI, Utils

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


class Item:
    def __init__(self):
        pass


def get_items_from_db():
    cur = cs_db.cursor()
    query = 'SELECT * FROM items_for_track'
    return cur.execute(query).fetchall()


def get_item_listings(market_hash_name):
    return steamAcc.get_item_listigs_only_first_10(market_hash_name)


def get_price_sm(itemnameid_):
    buy_price, _, _, _ = steamAcc.get_steam_prices(itemnameid_)
    return buy_price


def get_item_float_and_stickers(inspect_link):
    url = 'http://192.168.0.14/'
    params = {
        'url': inspect_link
    }
    response = requests.get(url, params=params)
    if response.status_code != 200:
        print('Get float and stickers:', response)
    response = response.json()
    iteminfo = response['iteminfo']
    float_item = iteminfo['floatvalue']
    stickers = iteminfo['stickers']
    stickers_result = []
    for sticker in stickers:
        if 'wear' in sticker:
            continue
        stickers_result.append({'slot': sticker['slot'], 'name': 'Sticker | '+sticker['name']})

    return float_item, stickers_result


def get_price_csm(market_hash_name):
    return csmoney_acc.get_price(market_hash_name)


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
        items = csmoney_acc.get_sticker_overpay(item_name, sticker, csm_price=csm_price)
        if 'error' in items:
            continue
        items = items['items']
        desired_stickers = filter_stickers(items, sticker)  # Инфа о скинах с этой наклейкой найденые на cs money
        sticker_price = currency.change_currency(desired_stickers[0]['price'])
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
        sticker['min_overpay'] = round(currency.change_currency(overpay_min))
        sticker['max_overpay'] = round(currency.change_currency(overpay_max))
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
    cur = cs_db.cursor()
    query = f'INSERT INTO checked (item_id, item_name) VALUES ({item_id}, "{item_name}")'
    cur.execute(query)
    cs_db.commit()


def check_handled_items(item_id):
    cur = cs_db.cursor()
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
                price_sm = (item['converted_price'] + item['converted_fee']) / 100
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
                bot.send_message(368333609, 'Get Float Failed')
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
                       f"🚀 Профит min: {profit_min}%\n" \

            print(message)
            if profit_min >= min_limit_profit or sum_prices_stickers > min_limit_stickers_price \
                    or sum_price_strick > min_limit_strick_price:
                bot.send_message(368333609, message)  # Я

    except AttributeError:
        print(listings)


def main():
    start = 0
    counter = start
    items = get_items_from_db()
    print(items)
    t1 = time.time()
    for item in items[start::]:

        item_name, link, _, _, _ = item
        print('-------------------------------------------------------------')
        print(f"Предмет {counter} из {len(items)}")
        counter += 1
        listings = get_item_listings(item_name)
        if not (handle_listings(item_name, link, listings)):
            continue
        break

    print(time.time() - t1)


if __name__ == '__main__':
    steamAcc = SteamMarketAPI.SteamMarketMethods()
    bot = telebot.TeleBot('5096520863:AAHHvfFpQTH5fuXHjjAfzYklNGBPw4z57zA')
    cs_db = sqlite3.connect('./db/CS.db')
    print(steamAcc.steamclient.is_session_alive())

    csmoney_acc = CSMoneyAPI.CSMMarketMethods(None)

    min_limit_stickers_price = 200
    min_limit_strick_price = 90
    min_limit_profit = 10
    currency = Utils.Currensy()
    have_strick = True
    while True:
        main()
