import requests

url = 'https://inventories.cs.money/5.0/load_bots_inventory/730?limit=60&offset=0&priceWithBonus=30&sort=botFirst&stickerName1=Sticker%20%7C%20Vitality%20%28Gold%29%20%7C%202020%20RMR&withStack=true'
response = requests.get(url)
print(response)
print(response.json())