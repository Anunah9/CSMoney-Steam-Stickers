import requests

from StickerOverpayBot import start_cs_inspect_server
from utils import Utils


def get_item_float_and_stickers(inspect_link):
    url = 'http://192.168.0.14/'
    params_ = {
        'url': inspect_link
    }
    try:
        response = requests.get(url, params=params_)
    except requests.exceptions.ConnectionError:
        Utils.close_server()
        start_cs_inspect_server()
        response = requests.get(url, params=params_)

    response = response.json()
    print(response)
    iteminfo = response['iteminfo']
    float_item = iteminfo['floatvalue']
    stickers = iteminfo['stickers']
    stickers_result = []
    for sticker in stickers:
        print(sticker)
        if 'wear' in sticker:
            print(sticker['wear'])
            continue
        stickers_result.append({'slot': sticker['slot'], 'name': 'Sticker | ' + sticker['name']})
    print(stickers_result)
    return float_item, stickers_result


if __name__ == '__main__':
    url = 'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20S76561198187797831A35903716048D9962780611081275903'
    get_item_float_and_stickers(url)