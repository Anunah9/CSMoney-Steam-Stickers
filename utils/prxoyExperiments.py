import sqlite3
import threading
import time
from http.cookies import SimpleCookie
import aiohttp
import requests
from aiohttp_socks import ProxyConnector
import asyncio

global counter


async def fetch(url, ip):
    # print(f'http://{ip}')

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, proxy=f'http://{ip}', timeout=10) as resp:
                if resp.status == 200:
                    print(resp.status)
                    to_db('http', ip)
        except Exception as exc:

            print('Ошибка', exc)


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





class workingProxy:
    proxy = []


async def main(proxies):
    while True:
        url = 'https://steamcommunity.com/market/listings/730/AK-47%20%7C%20Slate%20%28Field-Tested%29'
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



if __name__ == '__main__':

    db = sqlite3.connect('../db/CS.db')
    proxies_new = requests.get('https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt').text.split('\n')

    print(proxies_from_db)


    asyncio.get_event_loop().run_until_complete(main(proxies_new))
