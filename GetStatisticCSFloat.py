import json
import os
import sqlite3
import sys
import time

import requests


def get_items_from_db():
    cursor = conn.cursor()
    query = 'SELECT * FROM itemsForTrackCSFloatStatistic'
    items = cursor.execute(query).fetchall()
    print(items)
    return items


def get_statistic_from_CSF(item_name):
    url = f'https://csfloat.com/api/v1/history/{item_name}/sales'
    response = requests.get(url)
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
            data["created_at"],
            data["type"],
            data["price"]/100,
            data["state"],
            data["reference"]["base_price"]/100 if 'base_price' in data['reference'] else None,
            data["reference"]["float_factor"] if 'float_factor' in data['reference'] else None,
            data["reference"]["predicted_price"]/100 if 'predicted_price' in data['reference'] else None,
            data["reference"]["quantity"] if 'quantity' in data['reference'] else None,
            data["reference"]["last_updated"] if 'last_updated' in data['reference'] else None,
            data["item"]["float_value"],
            data["item"]["market_hash_name"],
            data["item"]["inspect_link"],
            data["item"]["scm"]["price"]/100,
            data["item"]["scm"]["volume"],
            data["is_seller"],
            data["is_watchlisted"],
            data["watchers"],
            data["sold_at"]
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


def main():
    items = get_items_from_db()
    for item in items:
        item_name = item[0]
        item_info = get_statistic_from_CSF(item_name)
        for item_listing in item_info:
            if 'stickers' in item_listing['item']:
                if not check_db(item_listing["id"]):
                    print('Добавляю')
                    to_db(item_listing)


if __name__ == '__main__':
    conn = sqlite3.connect('./db/CS.db')
    counter = 0
    while True:
        try:

            main()
            time.sleep(60*30)
        except Exception as exc:
            print(exc)
            restart_program()

