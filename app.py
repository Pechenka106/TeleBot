import telebot
import traceback

from sys import argv
from datetime import *
from calendar import monthrange
from telebot.apihelper import ApiTelegramException as Telebot_errors

from menu import *


class TokenError(Exception):
    pass


COMMANDS = {
    '/start': 'Приветствие',
    '/help': 'Помощь',
    '/menu': 'Главное меню'
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
    6: ('вс', 'воскресенье')
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
ALWAYS_RESTART = False
TOKEN_PATH = path('token.txt')


def main():
    args = argv
    global TOKEN_PATH
    global ALWAYS_RESTART
    if len(args) > 1:
        TOKEN_PATH = args[1].lstrip('token_path=')
    if len(args) > 2:
        ALWAYS_RESTART = bool(args[2].lstrip('restart='))
    if not os.path.isfile(TOKEN_PATH):
        raise TokenError(f"Token for bot not found in: \"{TOKEN_PATH}\"")
    bot = telebot.TeleBot(open(TOKEN_PATH, 'r', encoding='utf-8').readline(), parse_mode='html')
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

    @bot.message_handler(commands=['start'])
    def welcome(msg=None, call=None):
        last_name = ''
        if call:
            first_name = call.from_user.first_name
            if call.from_user.last_name:
                last_name = call.from_user.last_name
        else:
            first_name = msg.from_user.first_name
            if msg.from_user.last_name:
                last_name = msg.from_user.last_name
        start_menu = Menu(**MENUS['welcome']['params'],
                          text=f'Здравствуйте, <b>{"".join([last_name, first_name])}</b>!\n'
                               f'Записаться на прием Вы можете через главное меню по <b>кнопке</b> внизу, либо написав '
                               f'команду - <b>/menu</b>')
        if msg:
            bot.send_message(msg.chat.id, **start_menu.render())
            write_log(msg.from_user, f'Вызвал приветствие')
            return
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, **start_menu.render())
        write_log(call.from_user, f'Вызвал приветствие')

    @bot.message_handler(commands=['help'])
    def show_instruction(msg=None, call=None):
        help_menu = Menu(**MENUS['show_instruction']['params'],
                         text=f'Для открытия меню введите <b>/menu</b> или нажмите на кнопку <b>\"Главное меню\"</b>\n'
                              f'Чтобы записаться на прием к врачу выберите пункт <b>\"Записаться на прием\"</b>\n'
                              f'Чтобы посмотреть свои записи к врачам выберите пункт <b>\"Посмотреть мои записи\"</b>\n'
                              f'Чтобы отменить запись на прием выберите пункт <b>\"Убрать запись\"</b>')
        if msg:
            bot.send_message(msg.chat.id, **help_menu.render())
            write_log(msg.from_user, f'Посмотрел список команд с помощью \"/help\"')
            return
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, **help_menu.render())
        write_log(call.from_user, f'Посмотрел список команд с помощью кнопки \"Помощь\"')

    @bot.message_handler(commands=['menu', 'main_nemu'])
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
            write_log(msg.from_user, f'Открыл главное меню с помощью команды \"{msg.text}\"')
            return
        bot.send_message(chat_id=msg.chat.id, **main_menu__.render())
        write_log(msg.from_user, f'Открыл главное меню с помощью команды \"{msg.text}\"')

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
        write_log(call.from_user, f'Открыл главное меню с помощью кнопки \"Главное меню\"')

    @bot.callback_query_handler(func=lambda call: call.data.startswith('close_menu'))
    def close_menu(call):
        try:
            bot.delete_message(call.message.chat.id, call.message.id)
            write_log(call.from_user, f'Закрыл меню с помощью кнопки \"Закрыть\"')
        except Telebot_errors as error:
            bot.answer_callback_query(callback_query_id=call.id)
            write_log(call.from_user, f'Невозможно закрыть меню с помощью кнопки \"Закрыть\"\n{error}"')

    @bot.callback_query_handler(func=lambda call: call.data.startswith('create_appointment_menu'))
    def select_category_of_doctor(call):
        now = dt.now().strftime(f'%y%m%d%H%M')
        page = int(call.data.split(':')[1])
        data = edit_db(f'SELECT * FROM categories')
        if not data:
            bot.answer_callback_query(callback_query_id=call.id,
                                      text=f'К сожалению, у нас отсутствуют врачи в настоящее время')
            write_log(call.from_user, f'Пытался записаться на прием, но не было найдено врачей в клинике')
            return
        if not [i for i in
                edit_db(f"SELECT * FROM schedule WHERE user_id IS NULL")
                if int(''.join(map(str, i[1:6]))) >= int(now)]:
            bot.answer_callback_query(callback_query_id=call.id,
                                      text=f'К сожалению все места заняты')
            write_log(call.from_user, f'Пытался записаться на прием, но все места были заняты')
            return
        create_appointment_menu = Menu(
            buttons=[
                InlineKeyboardButton(text=elem[1], callback_data=f'selected_category:{elem[0]}:0')
                for elem in data
            ],
            **MENUS['create_appointment_menu']['params'],
        )
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                              **create_appointment_menu.render(page=page, call_data='create_appointment_menu'))

    @bot.callback_query_handler(func=lambda call: call.data.startswith('selected_category:'))
    def select_doctor(call):
        now = dt.now().strftime(f'%y%m%d%H%M')
        category_id, page = [int(i) if i.isnumeric() else i for i in call.data.split(':')[1:]]
        category = edit_db(f"SELECT title FROM categories WHERE id={category_id}")[0][0]
        if not [i[:10] for i in edit_db(f"SELECT * FROM schedule, doctors WHERE user_id IS NULL "
                                        f"AND schedule.doctor_id=doctors.id AND doctors.category_id={category_id}")
                if int(''.join(map(str, i[1:6]))) >= int(now)]:
            bot.answer_callback_query(callback_query_id=call.id,
                                      text=f'К сожалению, у нас отсутствуют свободные места у '
                                           f'{category}')
            write_log(call.from_user, f'Пытался выбрать врача {category}, но все места были заняты')
            return
        data = edit_db(f"SELECT id, last_name FROM doctors WHERE category_id={category_id}")
        if not data:
            bot.answer_callback_query(callback_query_id=call.id,
                                      text=f'К сожалению, у нас отсутствует врач - '
                                           f'{category}')
            write_log(call.from_user, f'Пытался записаться к врачу {category}, '
                                      f'но таких врачей не было в клинике')
            return
        select_doctor_menu = Menu(
            buttons=[
                InlineKeyboardButton(text=elem[1].lower().capitalize(),
                                     callback_data=f'selected_doctor:{elem[0]}:0')
                for elem in data
            ],
            **MENUS['select_doctor_menu']['params']
        )
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                              **select_doctor_menu.render(page=page, call_data='selected_category'))

    @bot.callback_query_handler(func=lambda call: call.data.startswith('selected_doctor:'))
    def select_year(call):
        now = dt.now().strftime(f'%y%m%d%H%M')
        doctor_id, page = [int(i) if i.isnumeric() else i for i in call.data.split(':')[1:]]
        years = [i[1] for i in
                 edit_db(f"SELECT * FROM schedule WHERE user_id IS NULL AND doctor_id={doctor_id}")
                 if int(''.join(map(str, i[1:6]))) >= int(now)]
        years = sorted(set(years))
        doctor = edit_db(f"SELECT categories.title, doctors.last_name, doctors.first_name FROM doctors, categories "
                         f"WHERE doctors.id={doctor_id} AND categories.id=doctors.category_id")[0]
        if not years:
            bot.answer_callback_query(callback_query_id=call.id,
                                      text=f'К сожалению все места к {doctor[0]}: {doctor[1]} {doctor[2]} уже заняты')
            write_log(call.from_user, f'Пытался выбрать врача с id {doctor_id}, но все места были заняты')
            # category_id = edit_db(f'SELECT category_id FROM doctors WHERE id={doctor_id}')[0][0]
            # call.data = f'selected_category:{category_id}:0'
            # select_doctor(call)
            return
        if len(years) == 1:
            call.data = f'selected_year:{doctor_id}:{years[0]}'
            select_month(call)
            return
        select_year_menu = Menu(
            buttons=[
                InlineKeyboardButton(text=f'20{elem}',
                                     callback_data=f'selected_year:{doctor_id}:{elem}')
                for elem in years
            ],
            **MENUS['select_year_menu']['params']
        )
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                              **select_year_menu.render(
                                  page=page, call_data=':'.join([str(i) for i in ('selected_doctor', doctor_id)])))

    @bot.callback_query_handler(func=lambda call: call.data.startswith('selected_year:'))
    def select_month(call):
        now = dt.now().strftime(f'%y%m%d%H%M')
        doctor_id, year = [int(i) if i.isnumeric() else i for i in call.data.split(':')[1:]]
        btns = []
        months = [i[2] for i in
                  edit_db(f"SELECT * FROM schedule WHERE user_id IS NULL AND doctor_id={doctor_id} "
                          f"AND year={year}")
                  if int(''.join(map(str, i[1:6]))) >= int(now)]
        months = sorted(set(months))
        if not months:
            bot.answer_callback_query(callback_query_id=call.id,
                                      text=f'К сожалению все места на {2000 + year} год заняты')
            write_log(call.from_user, f'Пытался выбрать время у врача с id {doctor_id} на {2000 + year}, '
                                      f'но все места были заняты')
            # call.data = ':'.join([doctor_id])
            # select_year(call)
            return
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
        now = dt.now().strftime(f'%y%m%d%H%M')
        doctor_id, year, month = [int(i) if i.isnumeric() else i for i in call.data.split(':')[1:]]
        pass_btn = InlineKeyboardButton(text=' ', callback_data='pass')
        days = [i[3] for i in edit_db(f"SELECT * FROM schedule WHERE user_id IS NULL "
                                      f"AND doctor_id={doctor_id} AND year={year} AND month={month}")
                if int(''.join(map(str, i[1:6]))) >= int(now)]
        days = sorted(set(days))
        if not days:
            bot.answer_callback_query(callback_query_id=call.id,
                                      text=f'К сожалению все места на {MONTH[month][1].capitalize()} уже заняты')
            write_log(call.from_user, f'Пытался выбрать время у врача с id {doctor_id} на {2000 + year}-{month}'
                                      f', но все места были заняты')
            # call.data = ':'.join([doctor_id, year])
            # select_month(call)
            return
        btns = [InlineKeyboardButton(text=WEEKDAY[index][0], callback_data='pass') for index in range(7)]
        btns += [pass_btn for _ in range(date(year=year, month=month, day=1).weekday())]
        for day in range(1, monthrange(year, month)[1] + 1):
            if day in days:
                btns.append(
                    InlineKeyboardButton(
                        text=str(day),
                        callback_data=f'selected_day:{doctor_id}:{year}:{month}:{day}:0'))
            else:
                btns.append(pass_btn)
        btns += [pass_btn for _ in range(len(btns) % 7)]
        select_day_menu = Menu(
            buttons=btns,
            **MENUS['select_day_menu']['params']
        )
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, **select_day_menu.render())

    @bot.callback_query_handler(func=lambda call: call.data.startswith('selected_day:'))
    def select_time(call):
        now = dt.now().strftime(f'%y%m%d%H%M')
        if call.data.count(':') == 5:
            doctor_id, year, month, day, page = [int(i) if i.isnumeric() else i
                                                 for i in call.data.split(':')[1:]]
        else:
            page = 0
            doctor_id, year, month, day = [int(i) if i.isnumeric() else i
                                           for i in call.data.split(':')[1:]]
        times = [(time(int(i[4]), int(i[5])), time(int(i[6]), int(i[7])), int(i[0]))
                 for i in edit_db(f"SELECT * FROM schedule WHERE "
                                  f"user_id IS NULL AND doctor_id={doctor_id} "
                                  f"AND year={year} AND month={month} AND day={day}")
                 if int(''.join(map(str, i[1:6]))) >= int(now)]
        times.sort(key=lambda elem: elem[0])
        if not times:
            bot.answer_callback_query(callback_query_id=call.id,
                                      text=f'К сожалению все места на {MONTH[month][1].capitalize()} {day} уже заняты')
            write_log(call.from_user, f'Пытался выбрать время у врача с id {doctor_id} на {2000 + year}-{month}'
                                      f'-{day}, но все места были заняты')
            # call.data = ':'.join([doctor_id, year, month])
            # select_day(call)
            return
        select_time_menu = Menu(
            buttons=[
                InlineKeyboardButton(text=f"{start.strftime('%H:%M')} - {end.strftime('%H:%M')}",
                                     callback_data=f'selected_time:{doctor_id}:{year}:{month}:{day}:{cell_id}')
                for start, end, cell_id in times
            ],
            **MENUS['select_time_menu']['params']
        )
        bot.edit_message_text(
            chat_id=call.message.chat.id, message_id=call.message.id,
            **select_time_menu.render(page, ':'.join(['selected_day', str(doctor_id),
                                                      str(year), str(month), str(day)])))

    def put_user_phone(msg, cell_id):
        phone = msg.text
        email = None
        edit_db(f"INSERT INTO users (id, username, first_name, last_name, email, phone) "
                f"VALUES (?, ?, ?, ?, ?, ?)",
                values=(
                    msg.from_user.id, msg.from_user.username, msg.from_user.first_name, msg.from_user.last_name, email,
                    phone))
        write_log(msg.from_user, f'Зарегистрировался в базе данных')
        edit_db(f"UPDATE schedule SET user_id={msg.from_user.id} WHERE id={cell_id}")
        markup = ReplyKeyboardRemove()
        data = [int(i) if str(i).isnumeric() else str(i) for i in
                edit_db(f"""SELECT title, last_name, first_name, middle_name, year, month, day, hour_start, 
                minute_start, hour_end, minute_end FROM categories, doctors, schedule 
                WHERE categories.id=doctors.category_id 
                AND doctors.id=schedule.doctor_id AND schedule.id={cell_id}""")[0]]
        text = f"{data[0]} - {' '.join([data[1], data[2], data[3]])} на " \
               f"{date(data[4] + 2000, data[5], data[6])} " \
               f"({WEEKDAY[date(data[4] + 2000, data[5], data[6]).weekday()][0].capitalize()}) в " \
               f"{time(data[7], data[8]).strftime('%H:%M')}-" \
               f"{time(data[9], data[10]).strftime('%H:%M')}"
        bot.send_message(msg.chat.id, f"Вы успешно записались к {text}",
                         reply_markup=markup)
        write_log(msg.from_user, f'Записался к {text}')

    @bot.callback_query_handler(func=lambda call: call.data.startswith('selected_time:'))
    def accept_appointment(call):
        cell_id = int(call.data.split(':')[-1])
        user = edit_db(f"""SELECT id FROM users WHERE id={call.from_user.id}""")
        try:
            bot.delete_message(call.message.chat.id, call.message.id)
        except Telebot_errors as error:
            write_log(user=call.from_user, message=f'Невозможно закрыть {error}')
        cell = edit_db(f'SELECT * FROM schedule WHERE id={cell_id}')[0]
        if not cell:
            year, month, day, time_start, time_end, doctor_id = \
                (cell[1], cell[2], cell[3], time(hour=cell[4], minute=cell[5]), time(hour=cell[6], minute=cell[7]),
                 cell[8])
            bot.answer_callback_query(
                callback_query_id=call.id,
                text=f'К сожалению все места на {MONTH[month][1].capitalize()} '
                     f'{day}:{time_start.strftime("%H%M")}-{time_end.strftime("%H%M")} уже заняты')
            write_log(call.from_user,
                      f'Пытался выбрать время у врача с id {doctor_id} на {2000 + year}-{month}-{day}:'
                      f'{time_start.strftime("%H%M")}-{time_end.strftime("%H%M")}, но все места были заняты')
            return
        if not user:
            markup = ReplyKeyboardMarkup()
            markup.add(KeyboardButton(text='Поделиться номером телефона', request_contact=True))
            msg = bot.send_message(text='Отправьте номер телефона чтобы записаться на прием',
                                   chat_id=call.message.chat.id, reply_markup=markup)
            bot.register_next_step_handler(msg, put_user_phone, cell_id)
            return
        edit_db(f"""UPDATE schedule SET user_id={call.from_user.id} WHERE id={cell_id}""")
        markup = ReplyKeyboardRemove()
        data = [int(i) if str(i).isnumeric() else str(i) for i in
                edit_db(f"""SELECT title, last_name, first_name, middle_name, year, month, day, hour_start, 
                minute_start, hour_end, minute_end FROM categories, doctors, schedule 
                WHERE categories.id=doctors.category_id AND doctors.id=schedule.doctor_id 
                AND schedule.id={cell_id}""")[0]]
        text = f"{data[0]} - {' '.join([data[1], data[2], data[3]])} на " \
               f"{date(data[4] + 2000, data[5], data[6])} " \
               f"({WEEKDAY[date(data[4] + 2000, data[5], data[6]).weekday()][0].capitalize()}) в " \
               f"{time(data[7], data[8]).strftime('%H:%M')}-" \
               f"{time(data[9], data[10]).strftime('%H:%M')}"
        bot.send_message(call.message.chat.id,
                         f"Вы успешно записались к {text}",
                         reply_markup=markup)
        write_log(call.from_user, f'Записался к {text}')

    @bot.callback_query_handler(func=lambda call: call.data.startswith('show_appointment_menu:'))
    def show_appointment_menu(call):
        now = dt.now().strftime(f'%y%m%d%H%M')
        page = int(call.data.split(':')[1])
        appointments = [[int(i) if str(i).isnumeric() else str(i) for i in appointment] for appointment in
                        edit_db(f"SELECT schedule.id, title, last_name, first_name, middle_name, year, month, day,"
                                f"hour_start, minute_start, hour_end, minute_end FROM categories, doctors, schedule "
                                f"WHERE doctors.category_id=categories.id AND doctors.id=schedule.doctor_id "
                                f"AND schedule.user_id={call.from_user.id}")
                        if int(''.join(map(str, appointment[5:10]))) >= int(now)]
        if not appointments:
            bot.answer_callback_query(callback_query_id=call.id, text=f'У вас отсутствуют записи к врачам')
            return
        appointment_menu = Menu(
            buttons=[
                InlineKeyboardButton(
                    text=f"{elem[7]} {MONTH[elem[6]][1].capitalize()} {time(elem[8], elem[9]).strftime('%H:%M')}-"
                         f"{time(elem[10], elem[11]).strftime('%H:%M')}",
                    callback_data=f"show_appointment:{elem[0]}")
                for elem in appointments
            ],
            **MENUS['show_appointment_menu']['params']
        )
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                              **appointment_menu.render(page, ':'.join(['show_appointment_menu', ''])))
        write_log(call.from_user, f'Посмотрел свои записи на прием')

    @bot.callback_query_handler(func=lambda call: call.data.startswith('show_appointment:'))
    def show_appointment(call):
        appointment_id = int(call.data.split(':')[1])
        apt = [int(i) if str(i).isnumeric() else str(i) for i in
               edit_db(f"SELECT title, doctors.last_name, doctors.last_name, doctors.middle_name, year, month, day, "
                       f"hour_start, minute_start, hour_end, minute_end, schedule.id, users.id "
                       f"FROM categories, doctors, schedule, users WHERE doctors.category_id=categories.id "
                       f"AND doctors.id=schedule.doctor_id "
                       f"AND users.id=schedule.user_id AND schedule.id={appointment_id}")[0]]
        year, month, day = edit_db(f'SELECT year, month, day FROM schedule WHERE id={appointment_id}')[0]
        bot.answer_callback_query(callback_query_id=call.id,
                                  text=f"Вы записаны к {apt[0]} - {' '.join((apt[1], apt[2], apt[3]))} на "
                                       f"{MONTH[apt[5]][1].capitalize()} {apt[6]} "
                                       f"({WEEKDAY[date(year=year, month=month, day=day).weekday()][0].capitalize()}) в"
                                       f" {time(apt[7], apt[8]).strftime('%H:%M')}-"
                                       f"{time(apt[9], apt[10]).strftime('%H:%M')}\n"
                                       f"Ваш номерок на прием: {apt[11]}-{apt[12]}",
                                  show_alert=True)
        write_log(call.from_user, f'Посмотрел свою запись с id {appointment_id}')

    @bot.callback_query_handler(func=lambda call: call.data.startswith('delete_appointment_menu:'))
    def show_delete_appointment_menu(call):
        now = dt.now().strftime(f'%y%m%d%H%M')
        page = int(call.data.split(':')[1])
        appointments = [[int(i) if str(i).isnumeric() else str(i) for i in appointment] for appointment in
                        edit_db(f"SELECT schedule.id, title, last_name, first_name, middle_name, year, month, day,"
                                f"hour_start, minute_start, hour_end, minute_end FROM categories, doctors, schedule "
                                f"WHERE doctors.category_id=categories.id AND doctors.id=schedule.doctor_id "
                                f"AND schedule.user_id={call.from_user.id}")
                        if int(''.join(map(str, appointment[5:10]))) >= int(now)]
        if not appointments:
            bot.answer_callback_query(callback_query_id=call.id, text=f'У вас отсутствуют записи к врачам')
            return
        appointment_menu = Menu(
            buttons=[
                InlineKeyboardButton(
                    text=f"{elem[7]} {MONTH[elem[6]][0].capitalize()} {time(elem[8], elem[9]).strftime('%H:%M')}-"
                         f"{time(elem[10], elem[11]).strftime('%H:%M')}",
                    callback_data=f"delete_appointment:{elem[0]}")
                for elem in appointments
            ],
            **MENUS['delete_appointment_menu']['params']
        )
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                              **appointment_menu.render(page, ':'.join(['delete_appointment_menu', ''])))
        write_log(call.from_user, f'Посмотрел свои записи чтобы удалить')

    @bot.callback_query_handler(func=lambda call: call.data.startswith('delete_appointment:'))
    def delete_appointment(call):
        appointment_id = int(call.data.split(':')[1])
        apt = [int(i) if str(i).isnumeric() else str(i) for i in
               edit_db(f"SELECT title, doctors.last_name, doctors.last_name, doctors.middle_name, year, month, day, "
                       f"hour_start, minute_start, hour_end, minute_end, schedule.id, users.id "
                       f"FROM categories, doctors, schedule, users WHERE doctors.category_id=categories.id "
                       f"AND doctors.id=schedule.doctor_id "
                       f"AND users.id=schedule.user_id AND schedule.id={appointment_id}")[0]]
        edit_db(f"UPDATE schedule SET user_id=? WHERE id={appointment_id}", [None])
        bot.answer_callback_query(callback_query_id=call.id,
                                  text=f"Вы убрали запись к {apt[0]} - {' '.join((apt[1], apt[2], apt[3]))} на "
                                       f"{MONTH[apt[5]][1].capitalize()} {apt[6]} в "
                                       f"{time(apt[7], apt[8]).strftime('%H:%M')}-"
                                       f"{time(apt[9], apt[10]).strftime('%H:%M')}",
                                  show_alert=True)
        write_log(call.from_user, f'Убрал запись с id {appointment_id}')
        if not edit_db(f"SELECT * FROM schedule WHERE user_id={call.from_user.id}"):
            main_menu(call)
        call.data = 'delete_appointment_menu:0'
        show_delete_appointment_menu(call)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('show_instruction'))
    def redirect_to_instruction(call):
        show_instruction(call=call)

    bot.polling(none_stop=True)


if __name__ == '__main__':
    if os.path.isfile(path('error_info.txt')):
        with open(path('error_info.txt'), mode='w', encoding='utf=8') as file:
            file.write(f'{dt.now()} - Запуск')
    start_writing_log()
    if ALWAYS_RESTART:
        while True:
            try:
                main()
            except Telebot_errors as error:
                traceback.print_exc()
                write_log(message='Перезапуск бота')
                tm.sleep(1)
            except Exception as error:
                traceback.print_exc()
                traceback.print_exc(file=open('error_info.txt', mode='w', encoding='utf-8'))
            finally:
                stop_writing_log()
    else:
        try:
            main()
        except Exception as error:
            traceback.print_exc()
            traceback.print_exc(file=open('error_info.txt', mode='w', encoding='utf-8'))
        finally:
            stop_writing_log()
