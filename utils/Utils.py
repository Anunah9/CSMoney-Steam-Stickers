import subprocess
import urllib.parse
from datetime import date

import requests
from pycbrf import ExchangeRates


def convert_price(price):
    return float(price.split(' ')[0].replace(',', '.'))


def convert_name(market_hash_name):
    return urllib.parse.quote(market_hash_name)


def get_pid_server():
    with open(r'C:\Users\Sasha\Desktop\CSGOFloatInspect\node_pid.txt') as f:
        pid = f.read()
        return pid


def close_server():
    pid = get_pid_server()
    print(f'PID запущенного процесса: {pid}')
    print('Выключаю сервер...')
    r = subprocess.run(['taskkill', '/F', '/T', '/PID', str(pid)], shell=True, stdout=subprocess.PIPE, text=True, encoding='cp866')
    text = r.stdout
    if text:
        process_id = text.split('процесса ')[1].split(',')[0]
        subprocess.run(['taskkill', '/F', '/T', '/PID', str(process_id)], shell=True, stdout=subprocess.PIPE, text=True,
                       encoding='cp866')
    print('Сообщение: ', r.stdout)

def close_bot(pid):
    print(f'PID запущенного процесса: {pid}')
    print('Выключаю бота...')
    r = subprocess.run(['taskkill', '/F', '/T', '/PID', str(pid)], shell=True, stdout=subprocess.PIPE, text=True,
                       encoding='cp866')
    text = r.stdout
    if text:
        process_id = text.split('процесса ')[1].split(',')[0]
        subprocess.run(['taskkill', '/F', '/T', '/PID', str(process_id)], shell=True, stdout=subprocess.PIPE, text=True,
                       encoding='cp866')
    print('Сообщение: ', r.stdout)


class Currensy:
    """USD, UAN, RUB"""
    today = date.today()
    rates = ExchangeRates(str(today), locale_en=True)
    start_currency = None
    target_currency = None

    def __init__(self, target_currency):
        self.target_currency = target_currency
        self.currency = self.get_steam_currency(target_currency)

    def change_currency(self, price):
        return price * self.currency

    def get_steam_currency(self, target_currency):
        url = f'https://api.steampowered.com/ISteamEconomy/GetAssetPrices/v1/?format=json&amp&appid=1764030&amp&key=97F914FB6333AC5416AF882DA9909A35'
        response = requests.get(url).json()
        currency = response['result']["assets"][0]['prices'][target_currency]/100
        print(currency)
        return currency