
import json
import os
import sqlite3
import sys
import time
from datetime import datetime

import requests


def replace_date_strings(date):
    date_format = "%Y-%m-%dT%H:%M:%S.%fZ"
    return datetime.strptime(date, date_format)


def get_items_from_db():
    cursor = conn.cursor()
    query = 'SELECT * FROM itemsForTrackCSFloatStatistic'
    items = cursor.execute(query).fetchall()
    print(items)
    return items


def get_statistic_from_CSF(item_name):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.5845.888 YaBrowser/23.9.2.888 Yowser/2.5 Safari/537.36'
    }
    url = f'https://csfloat.com/api/v1/history/{item_name}/sales'
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(response)
    return response.json()


def to_db(item_info):
    cursor = conn.cursor()
    data = item_info

    # Вставка информации о продаже в таблицу "sales"
    cursor.execute(
        """INSERT INTO salesCSFloat (id, created_at, type, price, state, base_price, float_factor, predicted_price, quantity, last_updated, float_value, market_hash_name, inspect_link, scm_price, scm_volume, is_seller, is_watchlisted, watchers, sold_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            data["id"],
            replace_date_strings(data["created_at"]),
            data["type"],
            data["price"]/100,
            data["state"],
            data["reference"]["base_price"]/100 if 'base_price' in data['reference'] else None,
            data["reference"]["float_factor"] if 'float_factor' in data['reference'] else None,
            data["reference"]["predicted_price"]/100 if 'predicted_price' in data['reference'] else None,
            data["reference"]["quantity"] if 'quantity' in data['reference'] else None,
            replace_date_strings(data["reference"]["last_updated"]) if 'last_updated' in data['reference'] else None,
            data["item"]["float_value"],
            data["item"]["market_hash_name"],
            data["item"]["inspect_link"],
            data["item"]["scm"]["price"]/100,
            data["item"]["scm"]["volume"],
            data["is_seller"],
            data["is_watchlisted"],
            data["watchers"],
            replace_date_strings(data["sold_at"])
        )
    )

    # Вставка информации о стикерах в таблицу "stickers"

    for sticker in data["item"]["stickers"]:

        cursor.execute(
            """INSERT INTO stickersForCSFloat (sale_id, sticker_id, slot, wear, icon_url, name, scm_price, scm_volume, 
            reference_price, reference_quantity, reference_updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                data["id"],
                sticker["stickerId"],
                sticker["slot"],
                sticker["wear"] if 'wear' in sticker else 0,
                sticker["icon_url"],
                sticker["name"],
                sticker["scm"]["price"]/100,
                sticker["scm"]["volume"],
                sticker["reference"]["price"]/100,
                sticker["reference"]["quantity"],
                sticker["reference"]["updated_at"]
            )
        )

        conn.commit()
        # print("Данные успешно записаны в базу данных.")


def restart_program():
    python = sys.executable
    os.execl(python, python, *sys.argv)


def check_db(sale_id):
    query = f'SELECT * FROM salesCSFloat WHERE id={sale_id}'
    cursor = conn.cursor()
    check = cursor.execute(query).fetchall()
    if check:
        return True
    else:
        return False


def get_start_position(action='get', position=None):
    cursor = conn.cursor()
    if action == 'get':
        query = 'SELECT number_start_statistic_csfloat FROM check_test'
        return cursor.execute(query).fetchone()[0]
    elif action == 'set':
        query = f'UPDATE check_test SET number_start_statistic_csfloat = {position}'
        cursor.execute(query)


def main():
    items = get_items_from_db()

    start = get_start_position('get')
    counter = start

    for item in items[start::]:
        print(f'Предмет: {counter} из {len(items)}')
        counter += 1
        item_name = item[0]
        item_info = get_statistic_from_CSF(item_name)
        for item_listing in item_info:
            if 'stickers' in item_listing['item']:
                if not check_db(item_listing["id"]):
                    print('Добавляю')
                    try:
                        to_db(item_listing)
                    except KeyError:
                        continue

        time.sleep(1)
        get_start_position('set', counter)


if __name__ == '__main__':
    conn = sqlite3.connect('./db/CS.db')

    while True:
        try:
            main()
            get_start_position('set', 0)
            time.sleep(60*15)
        except Exception as exc:
            print(exc)
            restart_program()

