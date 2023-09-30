import pprint
import time
from http.cookies import SimpleCookie
import requests
import telebot

import utils.CSMoneyAPI as csm


def parse_cookie_string(cookie_string):
    cookie_dict = {}
    cookies = cookie_string.split('; ')

    for cookie in cookies:
        key_value = cookie.split('=')
        if len(key_value) == 2:
            key = key_value[0]
            value = key_value[1]
            cookie_dict[key] = value

    return cookie_dict


def main():
    inventory = csmoney_acc.get_inventory()
    with_overstock = list(filter(lambda x: int(x['overstockDiff']) < 1 and x['defaultPrice'] > 0.8 and 'isMarket' not in x, inventory))
    while with_overstock:
        for idx, item in enumerate(with_overstock):
            print(idx)
            item_name = item['fullName']
            item_id = item['id']
            item_info = csmoney_acc.get_inventory_item_info(item_id)
            overstock = item_info['overstockDiff']

            message = f"🌟 **{item_name}** 🌟\n" \
                      f"Предметов до оверстока: {overstock}\n" \
                      # f"Ссылка: {item_link}\n"
            print(message)
            if overstock > 0:
                bot.send_message(368333609, message)  # Я
                with_overstock.pop(idx)
        time.sleep(10)


if __name__ == '__main__':
    raw_cookie = 'visitor_id=62c276de-e8e2-4453-b3be-fd65483b097c; BD_TEST=a; onboarding__skin_quick_view=false; region=Tatarstan Republic; auction__faq_banner=true; sc=868760AB-60B3-2DD8-21CD-43BFBF5E1EF9; AB_TEST_CONCRETE_SKIN_1_ITERATION=a; onboarding__withdraw=false; amp_d77dd0=fPIUdOWBOrsnPyEJjXy3vJ.NzY1NjExOTgxODc3OTc4MzE=..1h9d13q3q.1h9d13q8d.15.h.1m; amp_d77dd0_cs.money=fPIUdOWBOrsnPyEJjXy3vJ.NzY1NjExOTgxODc3OTc4MzE=..1h9d13qcg.1h9d13qcg.28.f.2n; trade_carts_open=false; isAnalyticEventsLimit=true; steamid=76561198187797831; avatar=https://avatars.steamstatic.com/fb98e69b0df5bb36975d58c26bdc9a1c28f1560a_medium.jpg; username=Anunah; registered_user=true; GleamId=nKZepUclJpOEMgB9s; GleamA=%7B%22nKZep%22%3A%22login%22%7D; csgo_ses=4ee25dfad52d71046273e2d99067db71d562dc3e91bf6aeae4d0240d649b3327; support_token=60b2fc39d94c5cb13d4c1beaa7cf3cd276db59aff0827d49fc556b5512195a25; new_language=en'
    cookies = parse_cookie_string(raw_cookie)
    bot = telebot.TeleBot('5096520863:AAHHvfFpQTH5fuXHjjAfzYklNGBPw4z57zA')

    csmoney_acc = csm.CSMMarketMethods(cookies)
    main()
