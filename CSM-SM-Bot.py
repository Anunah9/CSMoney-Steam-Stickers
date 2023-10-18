import sqlite3
import time
from urllib.parse import quote
import telebot
import utils.SteamMarketAPI as Steam
import utils.CSMoneyAPI as CSMoney
import utils.Utils
from utils import Utils


def get_items_from_csm(offset):
    return csmAcc.get_items(min_price=1, max_price=30, offset=offset, has_rare_sticker=False)


def create_url(item_name, price, has_trade_lock: bool):
    url = 'https://cs.money/csgo/trade/'
    params = {
        'search': quote(item_name),
        'minPrice': price,
        'maxPrice': price + 0.01,
        'hasTradeLock': has_trade_lock
    }
    query_string = '&'.join([f'{key}={value}' for key, value in params.items()])
    full_url = f'{url}?{query_string}'
    return full_url


def get_profit(price_csm, price_sm_no_fee, price_avg):
    profit = (price_sm_no_fee/price_csm - 1)*100
    profit_avg = (price_avg/price_csm - 1)*100
    return profit, profit_avg


def get_from_db(item_name):
    query = f'SELECT * FROM tempSteamPrices WHERE itemName = "{item_name}"'
    item = cur.execute(query).fetchone()
    if item:
        item_name, price_sm, price_avg, count = item
        return item
    else:
        return None


def to_db(item_name, price_sm, price_avg, count):
    query = f'INSERT INTO tempSteamPrices VALUES ("{item_name}", {price_sm}, {price_avg}, {count})'
    cur.execute(query)
    csdb.commit()


def main(start, stop):
    for offset in range(start, stop):
        items = get_items_from_csm(offset*60)
        for item in items:
            print('------------------------------------------------------')
            item_name = item['fullName']
            price_csm = currensy.change_currency(item['price'])
            item_sm = get_from_db(item_name)
            if item_sm:
                _, price_sm, price_avg_sm, count = item_sm
            else:

                price_history_sm = steamAcc.get_price_history(item_name)
                price_history_sm = steamAcc.get_sales_for_days(price_history_sm, 7)
                price_history_peaks_sm = steamAcc.peak_history(price_history_sm)
                count = steamAcc.get_count_sales(price_history_peaks_sm)
                if count < min_limit_count:
                    continue
                price_avg_sm = steamAcc.get_avg_price(price_history_peaks_sm)
                price_listings_sm = steamAcc.get_item_listigs_only_first_10(item_name)
                try:
                    price_no_fee = price_listings_sm[list(price_listings_sm.keys())[0]]['converted_price']
                    fee = price_listings_sm[list(price_listings_sm.keys())[0]]['converted_fee']
                except AttributeError:
                    print('Ошибка')
                    price_no_fee = 0
                    fee = 0
                except KeyError:
                    print(price_listings_sm)
                    price_no_fee = 0
                    fee = 0

                price_sm = (price_no_fee + fee) / 100
                to_db(item_name, price_sm, price_avg_sm, count)

            market_hash_mame = Utils.convert_name(item_name)
            url = f'https://steamcommunity.com/market/listings/730/{market_hash_mame}'
            csm_url = create_url(item_name, item['price'], has_trade_lock=False)
            profit, profit_avg = get_profit(price_csm, price_sm*0.87, price_avg_sm*0.87)
            if profit > min_profit and profit_avg > min_profit:
                print(item_name)
                print(url)
                print(csm_url)
                print('Цена csm: ', price_csm)
                print('Цена steam: ', price_sm)
                print('Цена avg steam: ', price_avg_sm)
                print(f'Профт: {profit}%')
                print(f'Профт средний: {profit_avg}%')
                message = (
                    f'📦 Название товара: {item_name}\n'
                    f'🌐 URL: {url}\n'
                    f'🔗 CSM URL: {csm_url}\n'
                    f'💰 Цена CSM: {price_csm}\n'
                    f'💲 Цена Steam: {price_sm}\n'
                    f'💱 Цена средняя Steam: {price_avg_sm}\n'
                    f'📦 Количество продаж: {count}\n'
                    f'💰 Профит: {profit}%\n'
                    f'💲 Средний профит: {profit_avg}%'
                )
                bot.send_message(368333609, message)  # Я


if __name__ == '__main__':
    API = '5096520863:AAHHvfFpQTH5fuXHjjAfzYklNGBPw4z57zA'
    bot = telebot.TeleBot(API)
    csdb = sqlite3.connect('./db/CS.db')
    cur = csdb.cursor()
    cur.execute('DELETE FROM tempSteamPrices')
    steamAcc = Steam.SteamMarketMethods()
    csmAcc = CSMoney.CSMMarketMethods(None)
    currensy = utils.Utils.Currensy()
    min_profit = -14
    min_limit_count = 20
    t1 = time.time()
    main(0, 50)
    print('Время выполнения: ', time.time() - t1)
