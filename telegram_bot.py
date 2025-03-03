# # https://www.helenjoscott.com/2023/03/08/creating-a-python-telegram-bot-in-pycharm/
# # https://pytba.readthedocs.io/en/latest/quick_start.html
#
# # https://www.helenjoscott.com/2023/03/08/creating-a-python-telegram-bot-in-pycharm/
# # https://pytba.readthedocs.io/en/latest/quick_start.html
#
import json

from telebot import TeleBot
from telebot.types import Message
import threading
from pathlib import Path


class TOTPBot:
    def __init__(self, token, chat_id):
        self.totp_number = None
        self.token = token
        self.chat_id = chat_id
        self.bot = TeleBot(token=self.token)
        self.setup_handlers()
        self.polling_thread = None

    def setup_handlers(self):
        @self.bot.message_handler(commands=['start'])
        def send_welcome(message: Message):
            self.bot.reply_to(message, "Please enter a 6-digit code...")

        @self.bot.message_handler(func=lambda message: True)
        def handle_message(message: Message):
            if not message.text.isdigit() or len(message.text) != 6:
                self.totp_number = "0"
                self.bot.reply_to(message, "Invalid Number")
            else:
                self.totp_number = message.text
                self.bot.reply_to(message, "Valid Number")

            self.stop_polling()

    def start_polling(self):
        self.polling_thread = threading.Thread(target=self.bot.polling, kwargs={'non_stop': True})
        self.polling_thread.start()

    def stop_polling(self):
        self.bot.stop_polling()
        if self.polling_thread:
            self.polling_thread.join()

    def start(self):
        self.bot.send_message(chat_id=self.chat_id, text="Please provide a 6-digit code after entering /start..")
        self.start_polling()

    def get_totp(self):
        while self.totp_number is None:
            continue
        return self.totp_number


def get_totp_number():
    script_path = str(Path(__file__).parent) + '/cred.json'
    with open(script_path) as f:
        data = json.load(f)
    token = data['telegram']['token']
    chat_id = data['telegram']['chat_id']
    totp_bot = TOTPBot(token, chat_id)
    totp_bot.start()

    return totp_bot.get_totp()
