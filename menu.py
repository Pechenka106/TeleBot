from logger import *

MAIN_MENU_BTN = InlineKeyboardButton(text="Главное меню", callback_data='start_menu')
CLOSE_MENU_BTN = InlineKeyboardButton(text="Закрыть", callback_data='close_menu')


def list_split(lst: list, n: int = 10) -> tuple[list[list[InlineKeyboardButton]], int]:
    count = n
    result, spis = [], []
    for elem in lst:
        spis.append(elem)
        count -= 1
        if count == 0:
            result.append(spis[:])
            spis.clear()
            count = n
    if spis:
        result.append(spis)
    return result, len(result)


def create_buttons(buttons: list[InlineKeyboardButton] = None,
                   page: int = 0,
                   row_size: int = 3,
                   elem_on_page: int = 10,
                   is_flip: bool = False,
                   down_button: InlineKeyboardButton = None,
                   is_close_menu_btn: bool = True,
                   is_main_menu_btn: bool = True,
                   menu_buttons_on_one_line: bool = True,
                   call_data=None,
                   *args,
                   **kwargs
                   ) -> InlineKeyboardMarkup | None:
    if not buttons:
        markup = InlineKeyboardMarkup()
        if is_close_menu_btn and is_main_menu_btn and menu_buttons_on_one_line:
            markup.row(CLOSE_MENU_BTN, MAIN_MENU_BTN)
            return markup
        if is_close_menu_btn:
            markup.row(CLOSE_MENU_BTN)
        if is_main_menu_btn:
            markup.row(MAIN_MENU_BTN)
        return markup
    n_rows = len(buttons) // row_size
    if is_flip and row_size < 2:
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
    next_btn = InlineKeyboardButton(text="->", callback_data=f'{call_data}:{page + 1}')
    prev_btn = InlineKeyboardButton(text="<-", callback_data=f'{call_data}:{page - 1}')
    if is_flip:
        lst = []
        if not (page == 0 or abs(page) == n_page):
            if len(btns[-1]) + 2 <= row_size:
                btns[-1] = [prev_btn] + btns[-1][:]
            else:
                lst.append(prev_btn)
        if not (page == -1 or abs(page) == n_page - 1):
            if len(btns[-1]) + 2 <= row_size:
                btns[-1] = btns[-1][:] + [next_btn]
            else:
                lst.append(next_btn)
        btns.append(lst)
    # print(btns)
    for row in btns:
        markup.row(*row)
    if down_button:
        markup.row(down_button)
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
                 buttons=None,
                 row_size: int = 3,
                 elem_on_page: int = 10,
                 is_flip: bool = False,
                 down_button: InlineKeyboardButton = None,
                 is_close_menu_btn: bool = True,
                 is_main_menu_btn: bool = True,
                 menu_buttons_on_one_line: bool = True,
                 media=None,
                 *args,
                 **kwargs
                 ):
        if buttons is None:
            buttons = []
        self.text = text
        self.buttons = buttons
        self.row_size = row_size
        self.elem_on_page = elem_on_page
        self.is_flip = is_flip
        self.down_button = down_button
        self.is_close_menu_btn = is_close_menu_btn
        self.is_main_menu_btn = is_main_menu_btn
        self.menu_buttons_on_one_line = menu_buttons_on_one_line
        self.media = media
        self.args = args
        self.kwargs = kwargs

    def render(self, page: int = 0, call_data=None):
        result = {
            'reply_markup':
                create_buttons(buttons=self.buttons,
                               page=page,
                               row_size=self.row_size,
                               elem_on_page=self.elem_on_page,
                               is_flip=self.is_flip,
                               down_button=self.down_button,
                               is_close_menu_btn=self.is_close_menu_btn,
                               is_main_menu_btn=self.is_main_menu_btn,
                               menu_buttons_on_one_line=self.menu_buttons_on_one_line,
                               call_data=call_data),
            **self.kwargs
        }
        if not self.media:
            return result | {'text': self.text}
        return result | {'caption': self.text, 'media': self.media}


with open(path('data\\menu.json'), mode='r', encoding='utf-8') as file:
    MENUS = json.load(file)
