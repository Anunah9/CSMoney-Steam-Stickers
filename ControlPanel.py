import datetime
import sqlite3
import subprocess
import threading
import time
import telebot
from utils import Utils

# class TelegramBot:
API = '6713247775:AAEq_pT350E8rUuyaz8eSWvyMYawK1Iqz9c'
bot = telebot.TeleBot(API)


def start_bot1():
    working_time, delta_time = check_bot()
    if delta_time < 10:
        return bot.send_message(368333609,
                                f'Бот уже запущен, последний чек был в {datetime.datetime.fromtimestamp(working_time).time()}')
    print('Запускаю бота...')

    try:
        p1 = subprocess.Popen(['start', 'cmd', '/k', 'StartStickerOverpayBotAsync.bat'], shell=True)
    except Exception as e:
        print(f'Произошла ошибка при запуске сервера: {str(e)}')
    return bot.send_message(368333609, 'Запускаю бота')


def stop_bot1(message):
    cs_db = sqlite3.connect('./db/CS.db')
    cur = cs_db.cursor()
    query = 'SELECT pid_bot FROM check_test'
    pid = int(cur.execute(query).fetchone()[0])

    Utils.close_bot(pid)
    Utils.close_server()
    return bot.reply_to(message, 'Бот остановлен')


@bot.message_handler(commands=['start'])
def welcome(message):
    chat_id = message.chat.id
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    button_start = telebot.types.KeyboardButton(text="Запустить бота")
    keyboard.add(button_start)
    button_start = telebot.types.KeyboardButton(text="Остановить бота")
    keyboard.add(button_start)
    bot.send_message(chat_id,
                     'Добро пожаловать в бота сбора обратной связи',
                     reply_markup=keyboard)


@bot.message_handler(func=lambda message: message.text == "Запустить бота")
def start_bot(message):
    start_bot1()


@bot.message_handler(func=lambda message: message.text == 'Остановить бота')
def stop_bot(message):
    stop_bot1(message)


def check_bot():
    cs_db = sqlite3.connect('./db/CS.db')
    cur = cs_db.cursor()
    query = 'SELECT working_time_check FROM check_test'
    working_time = int(cur.execute(query).fetchone()[0])
    print(working_time)
    time_now = int(time.time())
    print(time_now)
    delta_time = time_now - working_time
    return working_time, delta_time


@bot.callback_query_handler(func=lambda call: call.data == 'cancel_start')
def cancel_start_bot(call):
    message = call.message
    chat_id = message.chat.id
    message_id = message.message_id
    bot_state.cancel_delay_start = True
    bot.edit_message_text(chat_id=chat_id, message_id=message_id,
                          text='Запуск остановлен')


def delay_start_bot():
    timer = 0
    while timer < 300:
        if bot_state.cancel_delay_start == True:
            return
        time.sleep(1)
        print(timer)
        timer += 1
    start_bot1()


def periodic_check():
    keyboard = telebot.types.InlineKeyboardMarkup()
    button_cancel = telebot.types.InlineKeyboardButton(text="Отменить запуск?",
                                                       callback_data='cancel_start')
    keyboard.add(button_cancel)
    while True:
        bot_state.cancel_delay_start = False
        working_time, delta_time = check_bot()
        if delta_time > 10:
            bot.send_message(368333609, 'Кажется бот выключен. Он будет включен автоматически через 5 минут. \nЕсли '
                                        'вы не хотите включать бота нажмите на кнопку', reply_markup=keyboard)
            t3 = threading.Thread(target=delay_start_bot, daemon=True)
            t3.start()
            t3.join()

        time.sleep(1800)


class BotState:
    cancel_delay_start = False


bot_state = BotState
t1 = threading.Thread(target=periodic_check, daemon=True)
t1.start()

bot.infinity_polling()
