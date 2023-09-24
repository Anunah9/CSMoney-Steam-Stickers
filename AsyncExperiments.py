import asyncio
import json
import sys
import time

import aiohttp
import requests
from bs4 import BeautifulSoup

from utils import Utils, SteamMarketAPI

if sys.platform:
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

async def fetch_data(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                return await response.text()
            else:
                return None


async def get_item_listigs_only_first_10(async_session: aiohttp.ClientSession,  market_hash_name):
    url = 'https://steamcommunity.com/market/listings/730/' + Utils.convert_name(market_hash_name)
    response = await async_session.get(url)

    if response.status != 200:
        print('Get listing item', response)
        return response.status
    return response


async def get_listings(response: aiohttp.ClientResponse):
    response_text = await response.text()
    soup = BeautifulSoup(response_text, 'lxml')
    info = soup.findAll('script', type="text/javascript")[-1]
    result_sting = info.text.split('g_rgListingInfo =')[1].split(';')[0]
    listings = json.loads(result_sting)
    return listings


async def create_async_session():
    headers = steamAcc.steamclient._session.headers  # Можете передать заголовки из вашей существующей сессии
    cookie_jar = steamAcc.steamclient._session.cookies
    sync_cookies = requests.utils.dict_from_cookiejar(cookie_jar)
    async_session = aiohttp.ClientSession(headers=headers, cookies=sync_cookies)
    return async_session


async def get_balance(session: aiohttp.ClientSession):
    response = await session.get('https://steamcommunity.com/profiles/76561198187797831/inventory/')
    print(await response.text())


async def main():
    names = [
        'AK-47 | Elite Build (Field-Tested)',
        'StatTrak™ AWP | Capillary (Field-Tested)',
        'AK-47 | Elite Build (Minimal Wear)',
        'AK-47 | Slate (Field-Tested)',
        'AK-47 | Slate (Battle-Scarred)',
    ]
    session = await create_async_session()
    tasks = []
    for name in names:
        tasks.append(get_item_listigs_only_first_10(session, name))
    results = await asyncio.gather(*tasks)

    # Результаты будут в том же порядке, что и в списке urls
    for result in results:
        if result:
            listings = await get_listings(result)
            print(listings)

    await session.close()


if __name__ == '__main__':
    steamAcc = SteamMarketAPI.SteamMarketMethods()
    t1 = time.time()

    for i in range(1):
        asyncio.run(main())

        # time.sleep(0.5)
    t2 = time.time() - t1
    print(t2)