import telebot
import traceback

from datetime import *
from calendar import monthrange

from menu import *


def main():
    class TokenError(Exception):
        pass


    COMMANDS = {
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


    @bot.message_handler(commands=['menu', 'start', 'main_nemu'])
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


    @bot.callback_query_handler(func=lambda call: call.data.startswith('create_appointment_menu'))
    def select_category_of_doctor(call):
        data = edit_db(f'SELECT * FROM categories')
        if not data:
            bot.answer_callback_query(callback_query_id=call.id,
                                      text=f'К сожалению, у нас отсутствуют врачи в настоящее время')
            return
        if not edit_db(f"SELECT * FROM schedule WHERE user_id IS NULL OR user_id=''"):
            bot.answer_callback_query(callback_query_id=call.id,
                                      text=f'К сожалению все места заняты')
            return
        create_appointment_menu = Menu(
            buttons=[
                InlineKeyboardButton(text=elem[1], callback_data=f'selected_category:{elem[0]}')
                for elem in data
            ],
            **MENUS['create_appointment_menu']['params']
        )
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, **create_appointment_menu.render())


    @bot.callback_query_handler(func=lambda call: call.data.startswith('selected_category:'))
    def select_doctor(call):
        category_id = [int(i) if i.isnumeric() else i for i in call.data.split(':')[1:]][0]
        if not edit_db(f"SELECT year, month, day FROM schedule, doctors WHERE doctors.id=schedule.doctor_id AND "
                       f"doctors.category_id={category_id} AND schedule.user_id IS NULL"):
            bot.answer_callback_query(callback_query_id=call.id,
                                      text=f'К сожалению, у нас отсутствуют свободные места у '
                                           f'{edit_db(f"SELECT title FROM categories WHERE id={category_id}")[0][0]}')
            return
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
        data = edit_db(f"""SELECT DISTINCT year FROM schedule WHERE user_id IS NULL AND doctor_id={doctor_id}""")
        if len(data) == 1:
            call.data = f'selected_year:{doctor_id}:{data[0][0]}'
            select_month(call)
            return
        select_year_menu = Menu(
            buttons=[
                InlineKeyboardButton(text=f'20{elem[0]}',
                                     callback_data=f'selected_year:{doctor_id}:{elem[0]}')
                for elem in data
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
                  user_id IS NULL AND year={year} AND doctor_id={doctor_id}""")]
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
                                      f"user_id IS NULL AND year={year} AND month={month} AND doctor_id={doctor_id}")]
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
                                     f"user_id IS NULL AND year={year} AND month={month} AND day={day} "
                                     f"AND doctor_id={doctor_id}")]
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
        edit_db(f"""INSERT INTO users (id, username, first_name, last_name, email, phone) VALUES (?, ?, ?, ?, ?, ?)""",
                values=(msg.from_user.id, msg.from_user.username, msg.from_user.first_name, msg.from_user.last_name, email,
                        phone))
        write_log(msg.from_user, f'зарегистрировался в базе данных')
        edit_db(f"""UPDATE schedule SET user_id={msg.from_user.id} WHERE id={cell_id}""")
        markup = ReplyKeyboardRemove()
        data = [int(i) if str(i).isnumeric() else str(i) for i in
                edit_db(f"""SELECT title, last_name, first_name, middle_name, year, month, day, hour_start, minute_start, 
                hour_end, minute_end FROM categories, doctors, schedule WHERE categories.id=doctors.category_id 
                AND doctors.id=schedule.doctor_id AND schedule.id={cell_id}""")[0]]
        text = f"{data[0]} - {' '.join([data[1], data[2], data[3]])} на "\
               f"{date(data[4] + 2000, data[5], data[6])} в {time(data[7], data[8]).strftime('%H:%M')}-"\
               f"{time(data[9], data[10]).strftime('%H:%M')}"
        bot.send_message(msg.chat.id, f"Вы успешно записались к {text}",
                         reply_markup=markup)
        write_log(msg.from_user, f'записался к {text}')


    @bot.callback_query_handler(func=lambda call: call.data.startswith('selected_time:'))
    def accept_appointment(call):
        cell_id = int(call.data.split(':')[-1])
        user = edit_db(f"""SELECT id FROM users WHERE id={call.from_user.id}""")
        bot.delete_message(call.message.chat.id, call.message.id)
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
                edit_db(f"""SELECT title, last_name, first_name, middle_name, year, month, day, hour_start, minute_start, 
                hour_end, minute_end FROM categories, doctors, schedule WHERE categories.id=doctors.category_id 
                AND doctors.id=schedule.doctor_id AND schedule.id={cell_id}""")[0]]
        text = f"{data[0]} - {' '.join([data[1], data[2], data[3]])} на "\
               f"{date(data[4] + 2000, data[5], data[6])} в {time(data[7], data[8]).strftime('%H:%M')}-"\
               f"{time(data[9], data[10]).strftime('%H:%M')}"
        bot.send_message(call.message.chat.id,
                         f"Вы успешно записались к {text}",
                         reply_markup=markup)
        write_log(call.from_user, f'записался к {text}')


    @bot.callback_query_handler(func=lambda call: call.data.startswith('show_appointment_menu:'))
    def show_appointment_menu(call):
        page = int(call.data.split(':')[1])
        appointments = [[int(i) if str(i).isnumeric() else str(i) for i in appointment] for appointment in
                        edit_db(f"SELECT schedule.id, title, last_name, first_name, middle_name, year, month, day,"
                                f"hour_start, minute_start, hour_end, minute_end FROM categories, doctors, schedule "
                                f"WHERE doctors.category_id=categories.id AND doctors.id=schedule.doctor_id "
                                f"AND schedule.user_id={call.from_user.id}")]
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
        write_log(call.from_user, f'Посмотрел свои записи')


    @bot.callback_query_handler(func=lambda call: call.data.startswith('show_appointment:'))
    def show_appointment(call):
        appointment_id = int(call.data.split(':')[1])
        apt = [int(i) if str(i).isnumeric() else str(i) for i in
               edit_db(f"SELECT title, doctors.last_name, doctors.last_name, doctors.middle_name, year, month, day, "
                       f"hour_start, minute_start, hour_end, minute_end, schedule.id, users.id "
                       f"FROM categories, doctors, schedule, users WHERE doctors.category_id=categories.id "
                       f"AND doctors.id=schedule.doctor_id "
                       f"AND users.id=schedule.user_id AND schedule.id={appointment_id}")[0]]
        bot.answer_callback_query(callback_query_id=call.id,
                                  text=f"Вы записаны к {apt[0]} - {' '.join((apt[1], apt[2], apt[3]))} на "
                                       f"{MONTH[apt[5]][0].capitalize()} {apt[6]} в "
                                       f"{time(apt[7], apt[8]).strftime('%H:%M')}-"
                                       f"{time(apt[9], apt[10]).strftime('%H:%M')}\n"
                                       f"Ваш номерок на прием: {apt[11]}-{apt[12]}",
                                  show_alert=True)
        write_log(call.deom_user, f'Посмотрел свою запись с id {appointment_id}')


    @bot.callback_query_handler(func=lambda call: call.data.startswith('delete_appointment_menu:'))
    def show_delete_appointment_menu(call):
        page = int(call.data.split(':')[1])
        appointments = [[int(i) if str(i).isnumeric() else str(i) for i in appointment] for appointment in
                        edit_db(f"SELECT schedule.id, title, last_name, first_name, middle_name, year, month, day,"
                                f"hour_start, minute_start, hour_end, minute_end FROM categories, doctors, schedule "
                                f"WHERE doctors.category_id=categories.id AND doctors.id=schedule.doctor_id "
                                f"AND schedule.user_id={call.from_user.id}")]
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
    def show_appointment(call):
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
        call.data = 'delete_appointment_menu:0'
        show_delete_appointment_menu(call)


    start_writing_log()
    bot.polling(none_stop=True)
    stop_writing_log()


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        traceback.print_exc(file=open('error_info.txt', mode='a+', encoding='utf-8'))
