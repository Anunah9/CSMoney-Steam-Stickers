import time

import grequests
import requests

from utils import SteamMarketAPI


def make_sync_requests():
    urls = ['https://steamcommunity.com/market/listings/730/AK-47%20%7C%20Elite%20Build%20%28Field-Tested%29',
            'https://steamcommunity.com/market/listings/730/StatTrak%E2%84%A2%20AK-47%20%7C%20Elite%20Build%20%28Well-Worn%29',
            'https://steamcommunity.com/market/listings/730/StatTrak%E2%84%A2%20AK-47%20%7C%20Elite%20Build%20%28Battle-Scarred%29',
            'https://steamcommunity.com/market/listings/730/AK-47%20%7C%20Elite%20Build%20%28Minimal%20Wear%29',
            'https://steamcommunity.com/market/listings/730/AK-47%20%7C%20Slate%20%28Field-Tested%29',
            'https://steamcommunity.com/market/listings/730/AK-47%20%7C%20Slate%20%28Minimal%20Wear%29',
            'https://steamcommunity.com/market/listings/730/AK-47%20%7C%20Slate%20%28Battle-Scarred%29',
            'https://steamcommunity.com/market/listings/730/AK-47%20%7C%20Slate%20%28Well-Worn%29']
    for url in urls:
        t2 = time.time()
        response = steamAcc.steamclient._session.get(url)
        print(response)
        print('Время запроса: ', time.time() - t2)


def handle_response(response, **kwargs):
    if response is not None:
        print(f"Received response for {response.url}: {response.status_code}")
        # Здесь можно добавить код для обработки данных из ответа
    else:
        print("Request failed")


def async_requests():
    urls = ['https://steamcommunity.com/market/listings/730/AK-47%20%7C%20Elite%20Build%20%28Field-Tested%29',
            'https://steamcommunity.com/market/listings/730/StatTrak%E2%84%A2%20AK-47%20%7C%20Elite%20Build%20%28Well-Worn%29',
            'https://steamcommunity.com/market/listings/730/StatTrak%E2%84%A2%20AK-47%20%7C%20Elite%20Build%20%28Battle-Scarred%29',
            'https://steamcommunity.com/market/listings/730/AK-47%20%7C%20Elite%20Build%20%28Minimal%20Wear%29',
            'https://steamcommunity.com/market/listings/730/AK-47%20%7C%20Slate%20%28Field-Tested%29',
            'https://steamcommunity.com/market/listings/730/AK-47%20%7C%20Slate%20%28Minimal%20Wear%29',
            'https://steamcommunity.com/market/listings/730/AK-47%20%7C%20Slate%20%28Battle-Scarred%29',
            'https://steamcommunity.com/market/listings/730/AK-47%20%7C%20Slate%20%28Well-Worn%29']
    t2 = time.time()
    # rs = (grequests.get(u, session=steamAcc.steamclient._session) for u in urls)
    rss = []
    for url in urls:
        response = grequests.get(url, session=steamAcc.steamclient._session)
        rss.append(response)
    responses = grequests.imap(rss, exception_handler=handle_response, size=len(urls)+5)
    for response in responses:
        handle_response(response)
    print(responses)
    print('Время запроса: ', time.time()-t2)


if __name__ == '__main__':
    steamAcc = SteamMarketAPI.SteamMarketMethods()
    t1 = time.time()
    iters = 50
    for i in range(iters):
        print(i)
        # if make_sync_requests():
        #     break
        if async_requests():
            break
        # time.sleep(1)
    timee = time.time() - t1
    print('Среднее время sync', timee/iters)
