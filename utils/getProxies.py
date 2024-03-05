import sqlite3
import time
from http.cookies import SimpleCookie

import bs4
import aiohttp
import requests
from aiohttp_socks import ProxyConnector
import asyncio

global counter


def get_proxies_from_site():
    headers = {
        'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 YaBrowser/24.1.0.0 Safari/537.36"
    }
    response = requests.get('https://hidemy.io/ru/proxy-list/', headers=headers)
    soup = bs4.BeautifulSoup(response.text, 'lxml')
    # print(soup)
    table = soup.find('table').find('tbody').findAll('tr')
    ips = {
        'HTTP': [],
        'HTTPS': [],
        'SOCKS5': []
           }
    for proxy in table:
        info = proxy.findAll('td')
        ip = info[0].text
        port = info[1].text
        type_proxy = info[4].text
        print(ip+':'+port)
        print(type_proxy)
        type_proxy_list = ips[type_proxy]
        type_proxy_list.append(ip+':'+port)
    return ips


async def fetch(url, ip):
    # print(f'http://{ip}')
    # connector = ProxyConnector.from_url(ip)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 YaBrowser/24.1.0.0 Safari/537.36"
    }
    raw_cookie = r'ActListPageSize=10; timezoneOffset=10800,0; Steam_Language=english; browserid=3054070074255876030; steamCurrencyId=5; wants_mature_content_apps=331470|2220360; recentlyVisitedAppHubs=367520%2C504230%2C331470%2C1625450%2C2220360%2C1623730; extproviders_730=steam; extproviders_440=steam; strInventoryLastContext=730_2; sessionid=ecae25cffb53c9e97a3fb161; steamCountry=RU%7Ca6dc946811bf15e25415ae03f3902cf2; steamLoginSecure=76561198187797831%7C%7CeyAidHlwIjogIkpXVCIsICJhbGciOiAiRWREU0EiIH0.eyAiaXNzIjogInI6MEU0MF8yM0Q5RUZCRV9CM0E1MiIsICJzdWIiOiAiNzY1NjExOTgxODc3OTc4MzEiLCAiYXVkIjogWyAid2ViOmNvbW11bml0eSIgXSwgImV4cCI6IDE3MDg5MzYwOTYsICJuYmYiOiAxNzAwMjA4MTk2LCAiaWF0IjogMTcwODg0ODE5NiwgImp0aSI6ICIwRUYzXzIzRkVEN0E0XzYzQzUyIiwgIm9hdCI6IDE3MDY1MzgyMDcsICJydF9leHAiOiAxNzI1MTA2ODQxLCAicGVyIjogMCwgImlwX3N1YmplY3QiOiAiMjE3LjIzLjE4Ni4xMTEiLCAiaXBfY29uZmlybWVyIjogIjIxNy4yMy4xODYuMTExIiB9.M6e4KpD4gAh3doSWqujklWZ4CB2ZuOeM2hTgnBvG9QODcl1VqD_jp3uwyxga5iYMjN5MD--3UWxnR6ECgy7hDQ; webTradeEligibility=%7B%22allowed%22%3A1%2C%22allowed_at_time%22%3A0%2C%22steamguard_required_days%22%3A15%2C%22new_device_cooldown_days%22%3A0%2C%22time_checked%22%3A1708848340%7D; tsTradeOffersLastRead=1708864526'
    cookie = SimpleCookie()
    cookie.load(raw_cookie)
    BUFF_COOKIE = {k: v.value for k, v in cookie.items()}
    async with aiohttp.ClientSession(headers=headers) as session:
        try:
            async with session.get(url, proxy=f'http://{ip}', timeout=4) as resp:
                if resp.status == 200:
                    print(resp.status)
                    to_db('http', ip)
        except Exception as exc:

            print('Ошибка', exc)


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

async def main(proxies):
    while True:
        url = 'https://steamcommunity.com/market/itemordershistogram?country=RU&language=english&currency=5&item_nameid=176240977&two_factor=0'
        # url = 'https://pypi.org/project/aiohttp-socks/'
        queue = asyncio.Queue()
        print(len(proxies))
        for ip in proxies:
            # создаем задачи
            task = fetch(url, ip)
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


def get_proxies_from_file(path):
    with open(path, 'r') as f:
        proxies = f.read().split('\n')
        return proxies


if __name__ == '__main__':

    db = sqlite3.connect('../db/CS.db')
    proxies1 = requests.get('https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt').text.split('\n')
    proxies2 = requests.get('https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/protocols/socks5/data.txt').text.split('\n')
    proxies3 = get_proxies_from_file('../proxies.txt')
    # proxies = get_proxies_from_site()['HTTP']
    print(proxies2)
    asyncio.get_event_loop().run_until_complete(main(proxies1 + proxies2))
