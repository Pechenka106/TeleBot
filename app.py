import telebot
import os

from datetime import datetime as dt
from logger import *
from menu import *


class TokenError(Exception):
    pass


COMMANDS = {

}


if not os.path.isfile(path('token.txt')):
    raise TokenError(f"Token for bot not found in: \"{path('token.txt')}\"")
bot = telebot.TeleBot(open(path('token.txt'), 'r', encoding='utf-8').readline(), parse_mode='html')
bot.set_my_commands([BotCommand(key[1:], COMMANDS[key]) for key in COMMANDS.keys()])


@bot.message_handler(commands=['start'])
def start_bot(msg):
    bot.send_message(msg.chat.id, f'')


@bot.message_handler(commands=['help'])
def show_command(msg, repeat: bool = False):
    if repeat:
        bot.edit_message_text(chat_id=msg.chat.id, message_id=msg.id, **Main_menu.render())
        return
    bot.send_message(chat_id=msg.chat.id, **Main_menu.render())


@bot.callback_query_handler(func=lambda call: call.data.startswith('start_menu'))
def main_menu(call):
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, **Main_menu.render())


@bot.callback_query_handler(func=lambda call: call.data.startswith('close_menu'))
def close_menu(call):
    bot.delete_message(call.message.chat.id, call.message.id)


@bot.callback_query_handler(func=lambda call: call.data.startswith('create_appointment'))
def select_category_of_doctor(call):
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, **Create_appointment_menu.render(0))


start_writing_log()
bot.infinity_polling()
stop_writing_log()
