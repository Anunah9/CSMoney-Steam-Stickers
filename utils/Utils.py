import urllib.parse
from datetime import date
from pycbrf import ExchangeRates


def convert_price(price):
    return float(price.split(' ')[0].replace(',', '.'))


def convert_name(market_hash_name):
    return urllib.parse.quote(market_hash_name)


class Currensy:
    today = date.today()
    rates = ExchangeRates(str(today), locale_en=True)

    def change_currency(self, price):
        usd = float(self.rates['USD'].value)
        return price * usd
