import json
import sqlite3

from pprint import pprint
from typing import Tuple, List, Any

from telebot.types import *
from telebot.types import InlineKeyboardMarkup

from logger import *

MAIN_MENU_BTN = InlineKeyboardButton(text="Главное меню", callback_data='start_menu')
CLOSE_MENU_BTN = InlineKeyboardButton(text="Закрыть", callback_data='close_menu')
NEXT_BTN = InlineKeyboardButton(text="", callback_data="")
PREV_BTN = InlineKeyboardButton(text="", callback_data="")


def edit_db(command: str, values: (list, tuple) = None):
    with sqlite3.connect(path('data\\Clinic.db')) as db:
        cur = db.cursor()
        try:
            if values:
                data = cur.execute(command, values).fetchall()
            else:
                data = cur.execute(command).fetchall()
            db.commit()
        except Exception as error:
            print(error)
            cur.execute(f"""CREATE TABLE doctors (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL UNIQUE,
                        last_name   TEXT    NOT NULL,
                        first_name  TEXT    NOT NULL,
                        middle_name TEXT,
                        category    TEXT    NOT NULL
                    );
                    """)
            cur.execute(f"""CREATE TABLE schedule (id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL,
                        day        REAL    NOT NULL,
                        time_start INTEGER NOT NULL,
                        time_end   INTEGER NOT NULL,
                        doctor_id  INTEGER NOT NULL,
                        user_id    INTEGER NOT NULL
                    );""")
            cur.execute(f"""CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL,
                        username   TEXT    NOT NULL,
                        first_name TEXT,
                        last_name  TEXT,
                        email      TEXT,
                        phone      TEXT
                    );
                    """)
            db.commit()
            return None
    return data


def list_split(lst: list, n: int = 10) -> tuple[list, int]:
    if n == 1:
        return [[i] for i in lst], len(lst)
    result = []
    # print(f'result - {result}')
    for i in range(len(lst) // n - 1):
        result.append(lst[i * n:(i + 1) * n + 1])
    # print(f'result - {result}')
    if not len(lst) % n:
        result.append(lst[len(lst) // n: -1])
    else:
        result.append(lst[(len(lst) // n - 1) * n:(len(lst) // n) * n])
    # print(f'result - {result}')
    if len(lst) % n == 1:
        result.append([lst[-1]])
    elif len(lst) % n:
        result.append(lst[(len(lst) // n) * n: -1] + [lst[-1]])
    # print(f'result - {result}')
    result = [i for i in result if i]
    n_page = len(result)
    # print(f'result - {result}')
    return result, n_page


def create_buttons(buttons: list[InlineKeyboardButton] = None,
                   page: int = 0,
                   row_size: int = 3,
                   elem_on_page: int = 10,
                   is_flip: bool = False,
                   is_close_menu_btn: bool = True,
                   is_main_menu_btn: bool = True,
                   menu_buttons_on_one_line: bool = True,
                   *args,
                   **kwargs
                   ) -> InlineKeyboardMarkup | None:
    n_rows = len(buttons) // row_size
    # print(f'n_rows: {n_rows}')
    if is_flip and row_size < 3:
        raise IndexError("Can not create switch buttons \'<-\' \'->\' on one line")
    if is_main_menu_btn and is_close_menu_btn and menu_buttons_on_one_line and row_size < 2:
        raise IndexError("Can not create \"Close_menu\" and \"Main menu\" buttons on one line")
    if len(buttons) % row_size:
        n_rows += 1
    if not ((page < 0 and abs(page) <= n_rows) or (0 <= page < n_rows)):
        raise IndexError('Index of page list out range')
    if row_size < 1:
        raise Exception('Кол-во столбцов не может быть меньше 1')
    if elem_on_page < row_size:
        raise Exception('Размер ряда не может превышать размер страницы')
    if not buttons:
        return buttons
    # print(f'n_rows: {n_rows}')
    # print(buttons)
    if is_flip:
        res = list_split(buttons, n=elem_on_page)
        lst_btns, n_page = res[0][page], res[1]
    else:
        lst_btns, n_page = buttons, 1
    # print(lst_btns)
    btns = []
    count = row_size
    lst = []
    for elem in lst_btns:
        lst.append(elem)
        count -= 1
        if count == 0:
            count = row_size
            if row_size == 1:
                btns.append(lst)
            else:
                btns.append(lst)
            lst = []
    if len(lst_btns) % row_size:
        if row_size == 1:
            btns.append(lst)
        else:
            btns.append(lst)
    # print(btns)
    markup = InlineKeyboardMarkup()
    if is_flip:
        lst = []
        if not (page == 0 or abs(page) == n_page):
            if len(btns[-1]) + 2 <= row_size:
                btns[-1] = [PREV_BTN] + btns[-1][:]
            else:
                lst.append(PREV_BTN)
        if not (page == -1 or abs(page) == n_page - 1):
            if len(btns[-1]) + 2 <= row_size:
                btns[-1] = btns[-1][:] + [NEXT_BTN]
            else:
                lst.append(NEXT_BTN)
        btns.append(lst)
    # print(btns)
    for row in btns:
        markup.row(*row)
    if is_close_menu_btn and is_main_menu_btn:
        if menu_buttons_on_one_line:
            markup.row(CLOSE_MENU_BTN, MAIN_MENU_BTN)
        else:
            markup.row(CLOSE_MENU_BTN)
            markup.row(MAIN_MENU_BTN)
    elif is_close_menu_btn:
        markup.row(CLOSE_MENU_BTN)
    elif is_main_menu_btn:
        markup.row(MAIN_MENU_BTN)
    return markup


class Menu:
    def __init__(self,
                 text: str = '',
                 buttons: list[InlineKeyboardButton] = None,
                 row_size: int = 3,
                 elem_on_page: int = 10,
                 is_flip: bool = False,
                 is_close_menu_btn: bool = True,
                 is_main_menu_btn: bool = True,
                 menu_buttons_on_one_line: bool = True,
                 media=None,
                 *args,
                 **kwargs
                 ):
        self.text = text
        self.buttons = buttons
        self.row_size = row_size
        self.elem_on_page = elem_on_page
        self.is_flip = is_flip
        self.is_close_menu_btn = is_close_menu_btn
        self.is_main_menu_btn = is_main_menu_btn
        self.menu_buttons_on_one_line = menu_buttons_on_one_line
        self.media = media
        self.args = args
        self.kwargs = kwargs

    def render(self, page: int = 0):
        result = {
            'reply_markup':
                create_buttons(buttons=self.buttons,
                               page=page,
                               row_size=self.row_size,
                               elem_on_page=self.elem_on_page,
                               is_flip=self.is_flip,
                               is_close_menu_btn=self.is_close_menu_btn,
                               is_main_menu_btn=self.is_main_menu_btn,
                               menu_buttons_on_one_line=self.menu_buttons_on_one_line),
            **self.kwargs
        }
        if not self.media:
            return result | {'text': self.text}
        return result | {'caption': self.text, 'media': self.media}


with open(path('data\\menu.json'), mode='r', encoding='utf-8') as file:
    MENUS = json.load(file)

Main_menu = Menu(
    buttons=[
        InlineKeyboardButton(text=MENUS['main_menu']['buttons'][key]['text'],
                             callback_data=MENUS['main_menu']['buttons'][key]['callback_data'])
        for key in MENUS['main_menu']['buttons'].keys()
    ],
    **MENUS['main_menu']['params']
)
print([text for text in edit_db(f'SELECT DISTINCT category FROM doctors ORDER BY category')])

Create_appointment_menu = Menu(
    buttons=[
        InlineKeyboardButton(text=text[0], callback_data=f'select_{text[0]}')
        for text in edit_db(f'SELECT DISTINCT category FROM doctors ORDER BY category')
    ],
    **MENUS['create_appointment']['params']
)
