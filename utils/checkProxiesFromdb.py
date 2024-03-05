import json
import sqlite3
import threading
import time
from http.cookies import SimpleCookie
import aiohttp
import aiohttp_socks
import bs4
import requests
from aiohttp_socks import ProxyConnector
import asyncio
from utils import SteamMarketAPI

global counter


async def fetch(url, ip):
    # print(f'http://{ip}')

    connector = ProxyConnector.from_url(ip)
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, proxy=f'http://{ip}', timeout=10) as resp:
                if resp.status == 200:
                    print(resp.status)
                    to_db('http', ip)
        except Exception as exc:

            print('Ошибка', exc)


async def get_listings_from_response(response_text):
    soup = bs4.BeautifulSoup(response_text, 'lxml')
    info = soup.findAll('script', type="text/javascript")[-1]
    result_sting = info.text.split('g_rgListingInfo =')[1].split(';')[0]
    listings = json.loads(result_sting)
    return listings


async def fetch_data(session, proxy):
    url = 'https://steamcommunity.com/market/listings/730/AK-47%20%7C%20Slate%20%28Field-Tested%29'
    session.headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, ' \
                                    'like Gecko) Chrome/106.0.0.0 YaBrowser/22.11.2.807 Yowser/2.5 ' \
                                    'Safari/537.36'
    session.headers['Referer'] = steamAccMain.headers['Referer']
    t1 = time.time()
    connector = ProxyConnector.from_url(f'socks5://user:password@{proxy}')
    responses = []
    async with aiohttp.ClientSession() as session:
        for i in range(5):
            try:
                response = await session.get(url, proxy=f'http://{proxy}', timeout=5)
                responses.append(response.status)
                if response.status != 200:
                    print(response.status)
                    db.cursor().execute(f'DELETE FROM workingProxies WHERE ip = "{proxy}"')
                    # print(f'DELETE FROM workingProxies WHERE ip = "{proxy}"')
                if response.status == 200:
                    data = await response.text()
                    listings = await get_listings_from_response(data)
                    print(f'Successful response from {url}: {listings}')
            except Exception as exc:
                print('Ошибка', exc)
                # db.cursor().execute(f'DELETE FROM workingProxies WHERE ip = "{proxy}"')
        print(responses)
        if not responses:
            return
        if not 200 in responses:
            db.cursor().execute(f'DELETE FROM workingProxies WHERE ip = "{proxy}"')
        # print(f'Использую прокси: {proxy}')

        # async with session.get(url) as response:
        print('Время одного запроса: ', time.time() - t1)


# check_proxy('122.155.223.165:10203')


async def worker(name, queue):
    while True:
        # Get a "work item" out of the queue.
        task = await queue.get()
        await task
        # Notify the queue that the "work item" has been processed.
        queue.task_done()


def to_db(type, ip):
    cur = db.cursor()
    query = f'INSERT INTO workingProxies VALUES ("{type}", "{ip}")'
    cur.execute(query)
    db.commit()


async def create_async_session(steamclient):
    headers = steamclient._session.headers  # Можете передать заголовки из вашей существующей сессии
    # print(steamclient._session.cookies)
    cookie_jar = steamclient._session.cookies
    sync_cookies = requests.utils.dict_from_cookiejar(cookie_jar)
    # print('ccccccccccc', cookie_jar.get_dict("steamcommunity.com"))
    async_session = aiohttp.ClientSession(headers=headers, cookies=cookie_jar.get_dict("steamcommunity.com"))
    return async_session


class workingProxy:
    proxy = []


async def main():
    while True:
        proxies_from_db = list(map(lambda x: x[0], db.cursor().execute('SELECT ip FROM workingProxies').fetchall()))
        session = await create_async_session(steamclient=steamAccMain.steamclient)
        url = 'https://steamcommunity.com/market/listings/730/AK-47%20%7C%20Slate%20%28Field-Tested%29'
        queue = asyncio.Queue()
        print(len(proxies_from_db))
        for ip in proxies_from_db:
            # создаем задачи
            task = fetch_data(session, ip)
            queue.put_nowait(task)
            # складываем задачи в список
        tasks = []
        for i in range(250):
            task = asyncio.create_task(worker(f'worker-{i}', queue))
            tasks.append(task)

        started_at = time.monotonic()
        await queue.join()
        total_slept_for = time.monotonic() - started_at
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        print('====')
        print(f'3 workers slept in parallel for {total_slept_for:.2f} seconds')
        db.commit()
        await session.close()
        time.sleep(4)


def get_proxies_from_file(path):
    with open(path, 'r') as f:
        proxies = f.read().split('\n')
        print(proxies)


if __name__ == '__main__':
    db = sqlite3.connect('../db/CS.db')
    # get_proxies_from_file('../proxies.txt')
    # steamAccMain = try_login('Sanek0904', 'Bazaranet101', 'Sanek0904.txt')
    steamAccMain = SteamMarketAPI.SteamMarketMethods('abinunas1976', 'PQIUZmqgCW1992', '../abinunas1976.txt')
    # proxies_new = requests.get('https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks5.txt').text.split(
    #     '\n')
    asyncio.get_event_loop().run_until_complete(main())
