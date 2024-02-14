import requests
# -*- coding: utf-8 -*-
import datetime
import sqlite3 as sql
import threading
import time
from os import path
import requests
import telebot
from utils import Database

bot = telebot.TeleBot('5096520863:AAHHvfFpQTH5fuXHjjAfzYklNGBPw4z57zA')


def get_items_from_db():
    pass

def get_listings():
    pass


def catch_data_from_buff():
    url = 'https://buff.163.com/api/market/goods?game=csgo&page_num=1 '
    response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                                                        '(KHTML, like Gecko) Chrome/114.0.0.0 YaBrowser/23.7.1.1140 '
                                                        'Yowser/2.5 Safari/537.36'}).json()
    items_from_buff = response.get('data').get('items')
    return items_from_buff


def check_profit(_price_buff, _stickers):

    profit = (_price_tm * 0.9 / _price_buff - 1) * 100
    profit_middle = (_middle_price * 0.9 / _price_buff - 1) * 100
    return profit, profit_middle


def main_sleep():
    global check
    check = 1
    _dt_now = datetime.datetime.now().second
    _dt_delay = 180 - (dt_now - 25)
    db_TM.full_update_db()
    threading.Timer(_dt_delay, main_sleep)
    check = 0


def main():
    global check
    items_from_buff_old = history
    print(items_from_buff_old)
    items_from_buff = catch_data_from_buff()
    print(items_from_buff)
    history.clear()
    for item in items_from_buff:
        if item in items_from_buff_old:
            items_from_buff.remove(item)
    for item in items_from_buff:
        if item in items_from_buff_old:
            items_from_buff.remove(item)
    for item in items_from_buff:

        market_hash_name = item['market_hash_name']
        price_buff = convert_price_to_RUB(float(item.get("quick_price")))
        id_buff = item.get('id')
        buff_link = f'https://buff.163.com/goods/{id_buff}'
        buff_img = item.get('goods_info').get("icon_url")

        price_tm = db_TM.get_min_price(market_hash_name)
        if price_tm:
            price_tm = price_tm[0] / 100
        else:
            continue

        if price_tm < min_limit_price or max_limit_price < price_tm:
            continue

        price_history = Database.PriceHistory(market_hash_name, db_statistic_path + 'sell_history.db', 7)

        if len(price_history.price_history) <= 1:
            continue
        price_history.delete_anomalies()

        avg_price, count_sell = price_history.get_middle_price_and_count()
        if count_sell < min_limit_count:
            continue

        volatility = price_history.get_price_volatility()
        if not volatility:
            volatility_value = 0
        else:
            volatility_value = sum(volatility)


        message = f"Название предмета: {market_hash_name}\n" \
                  f"Цены:\n" \
                  f"- Цена на Buff: {price_buff:.2f} (без комиссии)\n" \
                  f"- Цена на ТМ: {price_tm:.2f} (с учетом комиссии)\n" \
                  f"- Средняя цена на TM: {avg_price:.2f} (без комиссии)\n" \
                  f"- Средняя цена на ТМ: {avg_price * 0.9:.2f} (с учетом комиссии)\n" \
                  f"\nСтатистика:\n" \
                  f"- Количество продаж (по вашей статистике): {count_sell}\n" \
                  f"- Волатильность: {volatility_value}\n" \
                  f"\nПрофит:\n" \
                  f"- Профит: {round(profit)}% (разница между покупной и продажной ценами)\n" \
                  f"- Профит к средней цене: {round(profit_middle)}% (разница между покупной и средней ценами)\n" \
                  f"\nСсылки:\n" \
                  f"- Ссылка на Buff: {buff_link}\n" \
                  f"- Ссылка на ТМ: {tm_url}"

        print(message)
        print('--------------------------------------------------')
        if sticker_price > price*3 or profit > 200:
            bot.send_photo(368333609, buff_img, caption=message)


class Params:
    bot: telebot.TeleBot = None
    cs_db = sqlite3.connect('./db/CS.db')
    t_before_429 = None
    steamAccMain = None
    steamAccServer = None
    csm_acc = utils.CSMoneyAPI.CSMMarketMethods(None)
    reset_router = resetRouter.ResetRouter()
    currency = Utils.Currensy()
    get_float_error_counter = 0
    stickers_prices = cs_db.cursor().execute('SELECT * FROM CSMoneyStickerPrices').fetchall()
    first_start = True
    counter_requests = 0
    counter_for_too_many_request = 0

    def update_stickers_prices(self):
        Sticker_db_updater.main()

    def convert_stickers_to_dict(self):
        sticker_prices_dict = {}
        for sticker in self.stickers_prices:
            sticker_prices_dict[sticker[0]] = sticker[1]
        self.stickers_prices = sticker_prices_dict

    def determination_of_initial_parameters(self):
        self.bot = telebot.TeleBot(API)
        self.bot_error_logger = telebot.TeleBot(API_ErrorLogger)
        self.bot_error_logger.send_message(368333609, 'Запуск бота')  # Я
        self.steamAccMain = try_login('Sanek0904', 'Bazaranet101', 'Sanek0904.txt')
        # self.steamAccServer = try_login('abinunas1976', 'PQIUZmqgCW1992', './ServerAcc.txt')
        self.bot_error_logger.send_message(368333609,
                              f'Авторизация в стиме: {params.steamAccMain.steamclient.is_session_alive()}')  # Я
        print(params.steamAccMain.steamclient.is_session_alive())
        self.bot_error_logger.send_message(368333609, 'Запуск inspect сервера')  # Я
        # time.sleep(10)
        # close_server()
        self.bot_error_logger.send_message(368333609, 'Обновление цен на стикеры')
        self.update_stickers_prices()
        self.bot_error_logger.send_message(368333609, 'Готово')
        # start_cs_inspect_server()


def read_config(file_path):
    config = {}
    with open(file_path, 'r') as file:
        for line in file:
            key, value = line.strip().split('=')
            config[key] = value
    return config



if __name__ == '__main__':
    t1 = threading.Thread(target=print_hel, args=('bob',), daemon=True)
    t1.start()
    API = '5096520863:AAHHvfFpQTH5fuXHjjAfzYklNGBPw4z57zA'
    API_ErrorLogger = '6713247775:AAEq_pT350E8rUuyaz8eSWvyMYawK1Iqz9c'
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

    params.bot_error_logger.send_message(368333609, setting_message)  # Я
    params.t_before_429 = time.time()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
