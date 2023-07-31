import sqlite3
import time

import requests
from bs4 import BeautifulSoup


def to_db(cursor, con, links: list):
    for item in links:
        link = item[0]
        price = item[1]
        query = f'INSERT INTO items (link, price) VALUES ("{link}", "{price}")'
        cursor.execute(query)
    con.commit()


def update_db(links, cur):
    for item in links:
        link = item[0]
        price = item[1]
        query = f'UPDATE test SET price = "{price}" WHERE link = "{link}"'
        print(query)
        cur.execute(query)



def parse_links(url):
    links = []
    cookie = 'ActListPageSize=10; enableSIH=true; timezoneOffset=10800,0; Steam_Language=english; browserid=2720780142366232795; steamCurrencyId=5; totalproviders_730=buff163; extproviders_730=steam,buff163; strInventoryLastContext=730_2; sessionid=69f59162b4852f7562730df8; webTradeEligibility=%7B%22allowed%22%3A1%2C%22allowed_at_time%22%3A0%2C%22steamguard_required_days%22%3A15%2C%22new_device_cooldown_days%22%3A0%2C%22time_checked%22%3A1687754904%7D; steamCountry=RU%7Ca35a5da9cd6192b55c197c043a81d1b8; steamLoginSecure=76561198187797831%7C%7CeyAidHlwIjogIkpXVCIsICJhbGciOiAiRWREU0EiIH0.eyAiaXNzIjogInI6MEQxOV8yMjc1RENENV9FQzVDQiIsICJzdWIiOiAiNzY1NjExOTgxODc3OTc4MzEiLCAiYXVkIjogWyAid2ViIiBdLCAiZXhwIjogMTY4Nzg1NjI0NCwgIm5iZiI6IDE2NzkxMjgxMDIsICJpYXQiOiAxNjg3NzY4MTAyLCAianRpIjogIjBEMUZfMjJCQkNCQkNfQUVBMjgiLCAib2F0IjogMTY4Mjg1OTE3MCwgInJ0X2V4cCI6IDE3MDA3OTk1NTAsICJwZXIiOiAwLCAiaXBfc3ViamVjdCI6ICI1LjEwMS4yMC4xNjMiLCAiaXBfY29uZmlybWVyIjogIjUuMTAxLjIwLjE2MyIgfQ.9Itx4hIbe0GspRDncaEC3SXigEZwshmrfr-uRq16K2bI2jv2n3yz9tuRbARJg41382bEJ2Z8Zh8Gh6VPAloSBA; recentlyVisitedAppHubs=588650%2C730; app_impressions=730@2_9_100008_|632360@2_100100_100101_100106'
    response = requests.get(url, cookies=cookie)
    print(response)
    # while response != '<Response [200]>':
    #     time.sleep(5)
    #     response = requests.get(url, cookies=cookie)
    soup = BeautifulSoup(response.json()['results_html'], 'lxml')
    links_row = soup.find_all('a', class_='market_listing_row_link')
    for link in links_row:
        price = float(link.find('span', class_='normal_price').find(class_="normal_price").get('data-price'))/100
        links.append((link['href'], price))

    return links


def main():
    db = sqlite3.connect('CS.db')
    cur = db.cursor()
    for page in range(1, 180):
        print('Страница: ', page)
        url = f'https://steamcommunity.com/market/search/render/?query=&start={page * 100}&count=100&appid=730'
        print(url)
        links = parse_links(url)
        # to_db(cur, db, links)
        update_db(links, cur)
        db.commit()
        time.sleep(1)


if __name__ == "__main__":
    main()
