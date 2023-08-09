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
    with_overstock = list(filter(lambda x: int(x['overstockDiff']) < 1 and x['defaultPrice'] > 0.8, inventory))
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
    raw_cookie = ('visitor_id=62c276de-e8e2-4453-b3be-fd65483b097c; registered_user=true; BD_TEST=a; '
                  'onboarding__skin_quick_view=false; '
                  'amp_9e76ea=-n0ZXiKdhVLOttObLYhLe3.NzY1NjExOTgxODc3OTc4MzE=..1gcf1dh09.1gcf1ei94.5.3.8; '
                  'amp_c14fa5=3z98-G-lKgjQoBbxySvhao.NzY1NjExOTgxODc3OTc4MzE=..1gcf1dh0p.1gcf1ei95.3.3.6; '
                  'region=Tatarstan Republic; auction__faq_banner=true; '
                  'amp_d77dd0=fPIUdOWBOrsnPyEJjXy3vJ.NzY1NjExOTgxODc3OTc4MzE=..1h6mdhtao.1h6mdhtfi.12.g.1i; '
                  'amp_d77dd0_cs.money=fPIUdOWBOrsnPyEJjXy3vJ.NzY1NjExOTgxODc3OTc4MzE=..1h6mdhthn.1h6mdists.1r.e.29; '
                  'sc=868760AB-60B3-2DD8-21CD-43BFBF5E1EF9; __cflb=04dToSW2fHwgo6FnoYc76GfBcc8jrwsFhpSh978gep; '
                  'isAnalyticEventsLimit=true; GleamId=nKZepcLuI9yXAxFeB; GleamA=%7B%22nKZep%22%3A%22login%22%7D; '
                  'trade_carts_open=false; csgo_ses=c51de68c36a0003a660b6d337d15a22520ae01932c318e5fd64cd354161e70a5; '
                  'steamid=76561198187797831; '
                  'avatar=https://avatars.steamstatic.com/fb98e69b0df5bb36975d58c26bdc9a1c28f1560a_medium.jpg; '
                  'username=Anunah; support_token=d69a586c92d46c64fa16765c614a24081bf7103e563b8816055e7821055d68ee; '
                  'AB_TEST_CONCRETE_SKIN_1_ITERATION=a; AB_TEST_UXTR_981_CASHBACK=a; AB_TEST_UXTR_981_CASHBACK_V3=b; '
                  'AB_TEST_UXTR_981_CASHBACK_V2=b; new_language=en')
    cookies = parse_cookie_string(raw_cookie)
    bot = telebot.TeleBot('5096520863:AAHHvfFpQTH5fuXHjjAfzYklNGBPw4z57zA')

    csmoney_acc = csm.CSMMarketMethods(cookies)
    main()
