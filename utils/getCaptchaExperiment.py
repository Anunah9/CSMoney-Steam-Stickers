import random
import tkinter
from io import StringIO
from PIL import Image

import requests
import telebot
import wget
from bs4 import BeautifulSoup


def get_server_urls():
    params = {
        'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/120.0.0.0 YaBrowser/24.1.0.0 Safari/537.36"
    }
    response = requests.get('https://www.freeopenvpn.org/index.php?lang=ru', headers=params)
    soup = BeautifulSoup(response.content, 'lxml')
    print(response.content)
    urls = soup.findAll('a')[6:-4]
    urls_res = []
    for i in urls:
        if 'private' in i.get('href'):
            continue
        print('https://www.freeopenvpn.org/'+i.get('href'))
        password = input('Введите пожалуйста пароль для этого ip: ')
        urls_res.append(('https://www.freeopenvpn.org/'+i.get('href'), password))
    return urls_res


def get_captcha_img(url, password):
    print(url)
    response = requests.get(url)
    print(response)
    # print(response.text)
    soup = BeautifulSoup(response.text, 'lxml')
    captcha = soup.findAll('script')
    # for idx, i in enumerate(captcha):
    #     print(idx, i)
    try:
        img = str(captcha[8]).split('<img src="')[1].split('" ')[0]
    except IndexError:
        img = str(captcha[5]).split('<img src="')[1].split('" ')[0]

    params = {
        'Accept': "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'ru,en;q=0.9',
        'Cache-Control': 'no-cache',
        'Cookie': 'FreeOVPN_lang=ru',
        'Pragma': 'no-cache',
        'Referer': url,
        'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "YaBrowser";v="24.1", "Yowser";v="2.5"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': "Windows",
        'Sec-Fetch-Dest': 'image',
        'Sec-Fetch-Mode': 'no-cors',
        'Sec-Fetch-Site': 'same-origin',
        'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 YaBrowser/24.1.0.0 Safari/537.36"
    }
    response = requests.get(url='https://www.freeopenvpn.org/' + img, headers=params, stream=True)
    bot.send_photo(368333609, response.content)
    with open(f'./numbers/{password}_{random.randrange(0, 10000)}.png', 'wb') as f:
        f.write(response.content)

    print('https://www.freeopenvpn.org/' + img)


def main():
    urls = get_server_urls()
    print(len(urls))
    for i in range(10):
        for url, password in urls:
            get_captcha_img(url, password)


if __name__ == '__main__':
    API = '5096520863:AAHHvfFpQTH5fuXHjjAfzYklNGBPw4z57zA'
    bot = telebot.TeleBot(API)
    main()
