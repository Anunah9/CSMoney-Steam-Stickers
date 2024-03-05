import asyncio
import pickle
import time
import bufflogin
import requests
import selenium
from bufflogin import Buff
from pysteamauth.auth import Steam
from selenium import webdriver
from selenium.webdriver.common.by import By
import dill


class BuffBuyMethods:
    def __init__(self):
        self.chrome_options = webdriver.FirefoxOptions()
        self.useragent = f'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) ' \
                         f'Chrome/114.0.0.0 YaBrowser/23.7.3.824 Yowser/2.5 Safari/537.36'
        self.chrome_options.add_argument(self.useragent)  # Исправление: Добавить self.useragent
        self.driver = webdriver.Firefox(options=self.chrome_options)  # Исправление: Передать параметр options
        self.driver.get('https://buff.163.com/market/')
        # self.create_cookie()
        self.load_cookies()
        self.already_buy = None
        self.balance = None

        time.sleep(3)

    def sell_item_from_inventory(self, sell_id, sell_price):
        print('Выбираю предмет')

        for i in range(5):
            time.sleep(1)
            try:
                btn = self.driver.find_element(By.XPATH, f'//*[@id="{sell_id}"]')
                self.driver.execute_script("arguments[0].click();", btn)
                break
            except selenium.common.exceptions.NoSuchElementException:
                print('Попытка выбрать')
                time.sleep(1)
            return
        print("Кнопка продать")
        self.driver.find_element(By.XPATH, '//*[@id="shelve"]').click()
        print("Кнопка предупреждения о стикерах")
        time.sleep(2)
        for i in range(5):
            try:
                self.driver.find_element(By.XPATH, '/html/body/div[8]/div[2]/div[2]/a').click()
                time.sleep(3)
                break
            except selenium.common.exceptions.NoSuchElementException:
                print('Все ок')
            except selenium.common.exceptions.ElementNotInteractableException:
                print('Все ок')
        print('Ввожу цену')
        for i in range(5):
            try:
                self.driver.find_element(By.XPATH, '/html/body/div[6]/div[1]/div[2]/div/table/tbody/tr[2]/td[5]/div/input').send_keys(sell_price)
                break
            except selenium.common.exceptions.NoSuchElementException:
                time.sleep(1)
        time.sleep(3)
        print('Жму кнопку продать')
        self.driver.find_element(By.XPATH, '/html/body/div[6]/div[1]/div[3]/table/tbody/tr/td[2]/a').click()
        time.sleep(4)
        print('Жму кнопку последнюю')
        for i in range(5):
            try:
                btn1 = self.driver.find_element(By.XPATH, '/html/body/div[29]/div/div[2]/a[2]')
                self.driver.find_element(By.XPATH, '/html/body/div[30]/div/div[2]/div/span').click()
                self.driver.execute_script("arguments[0].click();", btn1)
                break
            except selenium.common.exceptions.NoSuchElementException:
                print('111')
                time.sleep(1)
        self.open_inventory_page()
        self.driver.refresh()
        time.sleep(5)

    def create_cookie(self):
        self.driver.execute_script('loginModule.steamLogin()')
        print('жду выполнение логина')
        login = input('Вы выполнили авторизацию?(y/n): ')
        if login.lower() == 'y':
            print('Сохраняю cookie')
            pickle.dump(self.driver.get_cookies(), open('cookies.bin', 'wb'))
            print('Готово')

    def buy_item(self, url, listing_id):
        self.driver.get(url)
        # input()
        btn = []
        # listing_id = input('Введите id предмета: ')
        # print(self.driver.find_element(By.XPATH, "/html/body").text)

        for i in range(5):
            try:
                btn = self.driver.find_element(By.XPATH, f'//*[starts-with(@id, "sell_order_{listing_id}")]/td[6]/a')
            except selenium.common.exceptions.NoSuchElementException:
                print('Page dont load yet')
                time.sleep(1)
        if not btn:
            return

        self.driver.execute_script("arguments[0].click();", btn)
        time.sleep(3)
        self.driver.find_element(By.XPATH, '//*[@id="j_popup_epay"]/div[2]/div[4]/a').click()
        time.sleep(4)
        # input('Ждем пока загрузится')
        for i in range(5):
            try:
                self.driver.find_element(By.XPATH, '//*[@id="j_popup_payed"]/div[2]/div/div[2]').click()

            except selenium.common.exceptions.NoSuchElementException:
                print('Page dont load yet')
                time.sleep(1)
            except selenium.common.exceptions.ElementNotInteractableException:
                print('Все ок')
                return

    def open_inventory_page(self):
        self.driver.get(
            'https://buff.163.com/market/steam_inventory?game=csgo#page_num=1&page_size=200&search=&state=all')

    def load_cookies(self):
        for cookie in pickle.load(open("./utils/cookies", "rb")):
            self.driver.add_cookie(cookie)
        # self.driver.refresh()
        # input()


if __name__ == '__main__':
    buff_acc = BuffBuyMethods()
    buff_acc.buy_item('https://buff.163.com/goods/921430', '1030750220-7DC6')
    # buff_acc.open_inventory_page()
