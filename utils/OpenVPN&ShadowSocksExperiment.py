import asyncio
import time

import aiohttp
import requests
import ifaddr


def get_adapters_ips():
    adapters = ifaddr.get_adapters()
    ips = []
    for adapter in adapters:
        if 'TAP-Windows' in adapter.nice_name:
            print("IPs of network adapter " + adapter.nice_name)
            ips.append(adapter.ips[1].ip)
    return ips


async def session_for_src_addr_async(addr: str) -> aiohttp.ClientSession:
    connector = aiohttp.TCPConnector(limit=0, local_addr=(addr, 0))
    session = aiohttp.ClientSession(connector=connector)
    return session


def session_for_src_addr(addr: str) -> requests.Session:
    """
    Create `Session` which will bind to the specified local address
    rather than auto-selecting it.
    """
    session = requests.Session()
    for prefix in ('http://', 'https://'):
        session.get_adapter(prefix).init_poolmanager(
            # those are default values from HTTPAdapter's constructor
            connections=requests.adapters.DEFAULT_POOLSIZE,
            maxsize=requests.adapters.DEFAULT_POOLSIZE,
            # This should be a tuple of (address, port). Port 0 means auto-selection.
            source_address=(addr, 0),
        )

    return session


def get_active_sessions(ips):
    sessions = []
    for ip in ips:
        session = session_for_src_addr(ip)
        try:
            response1 = session.get('https://httpbin.org/ip')
        except requests.exceptions.ConnectionError:
            continue
        sessions.append(session)
        print(response1)
    return sessions


async def get_active_async_sessions(ips):
    sessions = []
    for ip in ips:
        session = await session_for_src_addr_async(ip)
        try:
            response1 = await session.get('https://httpbin.org/ip')
        except aiohttp.client_exceptions.ClientConnectorError:
            continue
        sessions.append(session)
        print(response1)
    return sessions


async def main():
    ips = get_adapters_ips()
    sessions = await get_active_async_sessions(ips)
    for i in range(10):
        for session in sessions:
            t1 = time.time()
            async with session.get('https://steamcommunity.com/market/listings/730/AK-47%20%7C%20Elite%20Build%20('
                                   'Minimal%20Wear)') as response:
                print(response.status)
                # print(await response.text())
            t2 = time.time() - t1
            print('Время выполнения s1: ', t2)
    for session in sessions:
        await session.close()


asyncio.get_event_loop().run_until_complete(main())


# class Experiment2:
#     proxies = {
#             'http':'socks5://localhost:1081',
#             'https':'socks5://localhost:1081'
#     }
#     response = requests.get('https://httpbin.org/ip', proxies=proxies).text
#     print(response)
#     for i in range(10):
#         t1 = time.time()
#         response = requests.get('https://httpbin.org/ip', proxies=proxies).text
#         print(response)
#         t2 = time.time() - t1
#         print('Время выполнения s1: ', t2)
