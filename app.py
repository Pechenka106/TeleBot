import datetime

import telebot
import os

from datetime import *
from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP
from calendar import monthrange

from logger import *
from menu import *


class TokenError(Exception):
    pass


COMMANDS = {

}

CRUTCH = {
    'year': 'год',
    'month': 'месяц',
    'day': 'день'
}

WEEKDAY = {
    0: ('пн', 'понедельник'),
    1: ('вт', 'вторник'),
    2: ('ср', 'среда'),
    3: ('чт', 'четверг'),
    4: ('пт', 'пятница'),
    5: ('сб', 'суббота'),
    6: ('вс', 'Воскресенье')
}
MONTH = {
    1: ('янв', 'январь'),
    2: ('фев', 'февраль'),
    3: ('мар', 'март'),
    4: ('апр', 'апрель'),
    5: ('май', 'май'),
    6: ('июн', 'июнь'),
    7: ('июл', 'июль'),
    8: ('авг', 'август'),
    9: ('сен', 'сентябрь'),
    10: ('окт', 'октябрь'),
    11: ('ноя', 'ноябрь'),
    12: ('дек', 'декабрь')
}

# Show_appointment_menu = Menu(
#     buttons=[
#         InlineKeyboardButton(text=text, callback_data=f'')
#         for text in edit_db(f'SELECT day, time_start, time_end, (SELECT category) FROM')
#     ]
# )


if not os.path.isfile(path('token.txt')):
    raise TokenError(f"Token for bot not found in: \"{path('token.txt')}\"")
bot = telebot.TeleBot(open(path('token.txt'), 'r', encoding='utf-8').readline(), parse_mode='html')
bot.set_my_commands([BotCommand(key[1:], COMMANDS[key]) for key in COMMANDS.keys()])


def create_data_button(lst: list[tuple[int, date, time, time, int, int]]) -> dict[date: tuple[time, time]]:
    days = {}
    for elem in lst:
        day, start_time, end_time = elem[1], elem[2], elem[3]
        if dt.combine(day, start_time) < dt.now():
            continue
        if days.get(day):
            days[day].append([start_time, end_time])
        else:
            days[day] = [[start_time, end_time]]
    free_days = {}
    for key in days.keys():
        free_days[key] = (
            min([elem for elem in [i[0] for i in days[key]]]),
            max([elem for elem in [i[1] for i in days[key]]])
        )
    return free_days


@bot.message_handler(commands=['help'])
def show_command(msg, repeat: bool = False):
    main_menu__ = Menu(
        buttons=[
            InlineKeyboardButton(text=MENUS['main_menu']['buttons'][key]['text'],
                                 callback_data=MENUS['main_menu']['buttons'][key]['callback_data'])
            for key in MENUS['main_menu']['buttons'].keys()
        ],
        **MENUS['main_menu']['params']
    )
    if repeat:
        bot.edit_message_text(chat_id=msg.chat.id, message_id=msg.id, **main_menu__.render())
        return
    bot.send_message(chat_id=msg.chat.id, **main_menu__.render())


@bot.callback_query_handler(func=lambda call: call.data.startswith('start_menu'))
def main_menu(call):
    main_menu__ = Menu(
        buttons=[
            InlineKeyboardButton(text=MENUS['main_menu']['buttons'][key]['text'],
                                 callback_data=MENUS['main_menu']['buttons'][key]['callback_data'])
            for key in MENUS['main_menu']['buttons'].keys()
        ],
        **MENUS['main_menu']['params']
    )
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, **main_menu__.render())


@bot.callback_query_handler(func=lambda call: call.data.startswith('close_menu'))
def close_menu(call):
    bot.delete_message(call.message.chat.id, call.message.id)


@bot.callback_query_handler(func=lambda call: call.data.startswith('create_appointment'))
def select_category_of_doctor(call):
    data = edit_db(f'SELECT * FROM categories')
    if not data:
        bot.answer_callback_query(callback_query_id=call.id,
                                  text=f'К сожалению, у нас отсутствуют врачи в настоящее время')
        return
    create_appointment_menu = Menu(
        buttons=[
            InlineKeyboardButton(text=elem[1], callback_data=f'selected_category:{elem[0]}')
            for elem in data
        ],
        **MENUS['create_appointment']['params']
    )
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, **create_appointment_menu.render())


@bot.callback_query_handler(func=lambda call: call.data.startswith('selected_category:'))
def select_doctor(call):
    category_id = [int(i) if i.isnumeric() else i for i in call.data.split(':')[1:]][0]
    data = edit_db(f"SELECT id, last_name FROM doctors WHERE category_id={category_id}")
    if not data:
        bot.answer_callback_query(callback_query_id=call.id,
                                  text=f'К сожалению, у нас отсутствует врач - '
                                       f'{edit_db(f"""SELECT title FROM categories WHERE id={category_id}""")[0][0]}')
        return
    select_doctor_menu = Menu(
        buttons=[
            InlineKeyboardButton(text=elem[1].lower().capitalize(),
                                 callback_data=f'selected_doctor:{elem[0]}')
            for elem in data
        ],
        **MENUS['select_doctor_menu']['params']
    )
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, **select_doctor_menu.render())


@bot.callback_query_handler(func=lambda call: call.data.startswith('selected_doctor:'))
def select_year(call):
    doctor_id = int(call.data.split(':')[1])
    select_year_menu = Menu(
        buttons=[
            InlineKeyboardButton(text=f'20{elem[0]}',
                                 callback_data=f'selected_year:{doctor_id}:{elem[0]}')
            for elem in edit_db(f"""SELECT DISTINCT year FROM schedule WHERE 
            doctor_id={doctor_id} AND user_id IS NULL""")
        ],
        **MENUS['select_year_menu']['params']
    )
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, **select_year_menu.render())


@bot.callback_query_handler(func=lambda call: call.data.startswith('selected_year:'))
def select_month(call):
    doctor_id, year = [int(i) if i.isnumeric() else i for i in call.data.split(':')[1:]]
    btns = []
    months = [i[0] for i in
              edit_db(f"""SELECT DISTINCT month FROM schedule WHERE 
              doctor_id={doctor_id} AND year={year} AND user_id IS NULL""")]
    for month in range(1, 13):
        if month in months:
            btns.append(
                InlineKeyboardButton(text=f'{MONTH[month][0]}',
                                     callback_data=f'selected_month:{doctor_id}:{year}:{month}'))
        else:
            btns.append(InlineKeyboardButton(text=' ', callback_data='pass'))
    select_month_menu = Menu(
        buttons=btns,
        **MENUS['select_month_menu']['params']
    )
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, **select_month_menu.render())


@bot.callback_query_handler(func=lambda call: call.data.startswith('selected_month:'))
def select_day(call):
    doctor_id, year, month = [int(i) if i.isnumeric() else i for i in call.data.split(':')[1:]]
    pass_btn = InlineKeyboardButton(text=' ', callback_data='pass')
    days = [i[0] for i in edit_db(f"SELECT DISTINCT day FROM schedule WHERE "
                                  f"doctor_id={doctor_id} AND year={year} AND month={month} AND user_id IS NULL")]
    btns = [InlineKeyboardButton(text=WEEKDAY[index][0], callback_data='pass') for index in range(7)]
    btns += [pass_btn for _ in range(date(year=year, month=month, day=min(days)).weekday())]
    for day in range(monthrange(year, month)[1]):
        if day in days:
            btns.append(
                InlineKeyboardButton(
                    text=str(day),
                    callback_data=f'selected_day:{doctor_id}:{year}:{month}:{day}'))
        else:
            btns.append(pass_btn)
    btns += [pass_btn for _ in range(len(btns) % 7 + 1)]
    select_day_menu = Menu(
        buttons=btns,
        **MENUS['select_day_menu']['params']
    )
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, **select_day_menu.render())


@bot.callback_query_handler(func=lambda call: call.data.startswith('selected_day:'))
def select_time(call):
    if call.data.count(':') == 5:
        doctor_id, year, month, day, page = [int(i) if i.isnumeric() else i
                                             for i in call.data.split(':')[1:]]
    else:
        page = 0
        doctor_id, year, month, day = [int(i) if i.isnumeric() else i
                                       for i in call.data.split(':')[1:]]
    times = [(time(int(elem[0]), int(elem[1])), time(int(elem[2]), int(elem[3])), int(elem[4]))
             for elem in edit_db(f"SELECT hour_start, minute_start, hour_end, minute_end, id FROM schedule WHERE "
                                 f"doctor_id={doctor_id} AND year={year} AND month={month} AND day={day} "
                                 f"AND user_id IS NULL")]
    select_time_menu = Menu(
        buttons=[
            InlineKeyboardButton(text=f"{start.strftime('%H:%M')} - {end.strftime('%H:%M')}", callback_data='pass')
            for start, end, cell_id in times
        ],
        **MENUS['select_time_menu']['params']
    )
    bot.edit_message_text(
        chat_id=call.message.chat.id, message_id=call.message.id,
        **select_time_menu.render(page, ':'.join(['selected_day', str(doctor_id),
                                                 str(year), str(month), str(day)])))


@bot.callback_query_handler(func=lambda call: call.data.startswith('selected_time:'))
def accept_appointment(call):
    pass


start_writing_log()
bot.infinity_polling()
stop_writing_log()
