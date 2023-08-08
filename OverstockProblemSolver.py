from http.cookies import SimpleCookie

import requests
import utils.CSMoneyAPI


def convert_str_to_cookie(raw_cookies):
    cookie = SimpleCookie()
    cookie.load(raw_cookies)
    return {k: v.value for k, v in cookie.items()}


def main():
    pass


if __name__ == '__main__':
    raw_cookie = ('visitor_id=62c276de-e8e2-4453-b3be-fd65483b097c; registered_user=true; BD_TEST=a; '
                  'onboarding__skin_quick_view=false; '
                  'amp_9e76ea=-n0ZXiKdhVLOttObLYhLe3.NzY1NjExOTgxODc3OTc4MzE=..1gcf1dh09.1gcf1ei94.5.3.8; '
                  'amp_c14fa5=3z98-G-lKgjQoBbxySvhao.NzY1NjExOTgxODc3OTc4MzE=..1gcf1dh0p.1gcf1ei95.3.3.6; '
                  'region=Tatarstan Republic; steamid=76561198187797831; username=Anunah; '
                  'AB_TEST_CONCRETE_SKIN_1_ITERATION=a; '
                  'avatar=https://avatars.steamstatic.com/fb98e69b0df5bb36975d58c26bdc9a1c28f1560a_medium.jpg; '
                  'auction__faq_banner=true; AB_TEST_UXTR_981_CASHBACK=a; AB_TEST_UXTR_981_CASHBACK_V2=b; '
                  'amp_d77dd0=fPIUdOWBOrsnPyEJjXy3vJ.NzY1NjExOTgxODc3OTc4MzE=..1h6mdhtao.1h6mdhtfi.12.g.1i; '
                  'amp_d77dd0_cs.money=fPIUdOWBOrsnPyEJjXy3vJ.NzY1NjExOTgxODc3OTc4MzE=..1h6mdhthn.1h6mdists.1r.e.29; '
                  'AB_TEST_UXTR_981_CASHBACK_V3=b; sc=868760AB-60B3-2DD8-21CD-43BFBF5E1EF9; '
                  'isAnalyticEventsLimit=true; GleamId=nKZepLGyYphfbgwpk; '
                  'csgo_ses=340140bf41f7f884215300928597dc59b2743178f6f4b0482cbe7e37c339c3e9; '
                  'support_token=5db6b4dd312993997c5ed76cb7af082a643843ec2a36114a2e48d92d406f3d37; '
                  'GleamA=%7B%22nKZep%22%3A%22login%22%7D; __cflb=04dToSW2fHwgo6FnoYc76GfBcc8jrwsFhpSh978gep; '
                  'trade_carts_open=false; new_language=en')
    cookies = convert_str_to_cookie(raw_cookie)
    main()