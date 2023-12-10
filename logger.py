import sqlite3

from telebot.types import *
from datetime import datetime as dt
from pathlib import Path
import time as tm
from typing import *


DIR_PATH = Path.cwd()


def show_time_complete(func):
    def decorated(*args, **kwargs):
        start_time = tm.time()
        func(*args, **kwargs)
        end_time = tm.time()
        print(f'function {func.__name__} completed in {end_time - start_time} second')
    return decorated


def path(path_file: str = 'log.txt') -> str:
    return str(Path(DIR_PATH, path_file))


def edit_db(command: str,
            values: tuple | list = None,
            create_database: bool = False,
            path_to_database: str = path('data\\Clinic.db')):
    with sqlite3.connect(path_to_database) as db:
        cur = db.cursor()
        try:
            if values:
                data = cur.execute(command, values).fetchall()
            else:
                data = cur.execute(command).fetchall()
            db.commit()
        except Exception as error:
            print(command + '\n' + str(error))
            if not create_database:
                return None
            cur.execute(f"""CREATE TABLE doctors (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL UNIQUE,
                        last_name   TEXT    NOT NULL,
                        first_name  TEXT    NOT NULL,
                        middle_name TEXT,
                        category_id INTEGER NOT NULL);""")
            cur.execute(f"""CREATE TABLE schedule (id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL,
                        year         INTEGER NOT NULL,
                        month        INTEGER NOT NULL,
                        day          INTEGER NOT NULL,
                        hour_start   INTEGER NOT NULL,
                        minute_start INTEGER NOT NULL,
                        hour_end     INTEGER NOT NULL,
                        minute_end   INTEGER NOT NULL,
                        doctor_id    INTEGER NOT NULL,
                        user_id      INTEGER);""")
            cur.execute(f"""CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL,
                        username   TEXT    NOT NULL,
                        first_name TEXT,
                        last_name  TEXT,
                        email      TEXT,
                        phone      TEXT);""")
            cur.execute(f"""CREATE TABLE categories (id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL,
                        title TEXT UNIQUE NOT NULL);""")
            db.commit()
            return None
    return data


def start_writing_log():
    if not os.path.isfile(path()):
        new_log = open(path(), mode='w', encoding='utf-8')
        new_log.close()
    log_data = open(path(), 'r', encoding='utf-8').readlines()
    n = 0
    for i in log_data[::-1]:
        if 'Запуск №' not in i:
            continue
        try:
            n = int(i[i.index('№') + 1:-1])
        except Exception as error:
            print(error, file=open(path(), mode='a+', encoding='utf-8'))
            print(error)
        break
    print(f'----------------\n{dt.now()}: Запуск №{n + 1}\n')
    print(f'----------------\n{dt.now()}: Запуск №{n + 1}\n',
          file=open(path('log.txt'), mode='a+', encoding='utf-8'))


def write_log(user: User = None,
              message: str = 'DEBUG',
              only_str: bool = False,
              ending: str = '\n'):
    if (not user and message) or only_str:
        print(f'{dt.now()}: {message}', end=ending, file=open(path()))
        print(f'{dt.now()}: {message}', end=ending)
        return
    print(f'{dt.now()}: Пользователь - {user.username}: {user.id} '
          f'({user.first_name} {user.last_name}) *** {message}', end=ending)
    print(f'{dt.now()}: Пользователь - {user.username}: {user.id} '
          f'({user.first_name} {user.last_name}) *** {message}', end=ending,
          file=open(path(), mode='a+', encoding='utf-8'))


def stop_writing_log():
    print(f'{dt.now()}: Завершение работы\n----------------\n')
    print(f'{dt.now()}: Завершение работы\n----------------\n',
          file=open(path('log.txt'), mode='a+', encoding='utf-8'))
