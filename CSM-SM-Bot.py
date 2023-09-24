import requests
import utils.SteamMarketAPI as steam


def get_items_from_csm(offset):
    return []


def main():
    for offset in range(10):
        items = get_items_from_csm(offset*60)
        for item in items:
            price_csm = item['price']
            price_history_sm = steamAcc.get_price_history(item['name'])
            price_listings_sm = steamAcc.get_item_listigs_only_first_10(item['name'])
            price_sm = price_listings_sm[0]['price']


if __name__ == '__main__':
    steamAcc = steam.SteamMarketMethods()
    main()
