import os

import requests
import utils.SteamMarketAPI
steamAcc = utils.SteamMarketAPI.SteamMarketMethods()

for i in range(100):
    os.chdir('../')
    response = steamAcc.get_item_listigs_only_first_10('AK-47 | Phantom Disruptor (Field-Tested)')
    print(response)
