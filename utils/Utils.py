import urllib.parse
from datetime import date
from pycbrf import ExchangeRates


def convert_price(price):
    return float(price.split(' ')[0].replace(',', '.'))


def convert_name(market_hash_name):
    return urllib.parse.quote(market_hash_name)


def change_currency(price):
    today = date.today()

    rates = ExchangeRates(str(today), locale_en=True)
    usd = float(rates['USD'].value)
    return price * usd
