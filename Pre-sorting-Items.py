import sqlite3
import time
import traceback
from os import path
import utils


def get_items_from_db():
    types_deny = ['%Graffiti%', '%Souvenir%', '%Pin%', '%Music Kit%', '%Case%', '%Sticker%', '%Capsule%',
                  '%UMP-45%', '%Nova%', '%Sawed-Off%', '%PP-Bizon%', '%XM1014%', '%G3SG1%', '%Negev%',
                  '%R8 Revolver%', '%MAG-7%', '%SCAR-20%', '%P2000%', '%Patch%', '%Sealed%']
    types = ("%Gloves%", "%Wraps%", "%Knife%", "%Karambit%", "%Daggers%", "%Bayonet%")

    cur = db_cs.cursor()
    NOT_LIKE = ''
    LIKE = ''
    for _type in types_deny[1::]:
        LIKE += f' OR market_hash_name LIKE "{_type}"'
        NOT_LIKE += f' AND market_hash_name NOT LIKE "{_type}"'
    query = f'SELECT * FROM items WHERE market_hash_name NOT LIKE "{types[0]}"' + NOT_LIKE

    result = cur.execute(query).fetchall()
    return result


def to_db(con, item_, count):
    cur = con.cursor()
    query = f'INSERT INTO items_many_counts (market_hash_name, link, itemnameid, count) VALUES ("{item_[0]}", "{item_[1]}", ' \
            f'"{item_[2]}", "{count}")'
    cur.execute(query)
    con.commit()


def main():
    item_name = item[0]
    link = item[1]
    print(item_name)
    tm_price = db_TM.get_min_price(item_name)
    if tm_price:
        tm_price = tm_price[0] / 100
        if tm_price < min_limit_price or tm_price > max_limit_price:
            return False
    price_history = steamAcc.get_price_history(item_name)
    if not price_history:
        print('Price_history_err')
        return False
    price_history_days = steamAcc.get_sales_for_days(price_history, target_days)
    count = steamAcc.get_count_sales(price_history_days)
    to_db(db_cs, item, count)


if __name__ == '__main__':
    ## Посчитать минимальную цену продажи чтобы не уйти в минус и посмотреть сколько продаж выше этой цены и есть ли лоты выше такой цены

    steamAcc = utils.SteamMarketAPI.SteamMarketMethods()
    print(steamAcc.steamclient.is_session_alive())

    # bot = telebot.TeleBot('5096520863:AAHHvfFpQTH5fuXHjjAfzYklNGBPw4z57zA')
    db_TM = utils.Database.DatabaseTM()  # Обновляет базу данных ТМ при первом запуске
    db_TM.full_update_db()
    path_to_db = path.join(path.curdir, 'db') + path.sep
    db_cs = sqlite3.connect(path_to_db + 'CS.db')
    items = get_items_from_db()

    print(items[0])
    target_days = 14  # Период истории продаж в днях
    min_limit_price = 90
    max_limit_price = 300
    min_limit_count = 15

    start = 0
    counter = start
    try:
        for item in items[start::]:
            print('----------------------------------------------')
            print(f"Предмет {counter} из {len(items)}")
            print("Название: ", item[0])
            counter += 1
            try:
                if not main():
                    continue
            except TypeError:
                traceback.print_exc()
                continue

    except Exception:
        traceback.print_exc()
        # bot.send_message(368333609, 'Error')  # Я