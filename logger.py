import os
import sqlite3

from telebot.types import *
from datetime import datetime as dt
from pathlib import Path


DIR_PATH = Path.cwd()


def edit_db(command: str, values: (list, tuple) = None, create_database: bool = False):
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


def path(path_file: str = 'log.txt') -> str:
    return str(Path(DIR_PATH, path_file))


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


def write_log(user: User, message: str = 'DEBUG', only_str: bool = False):
    if only_str:
        print(f'{dt.now()}: {message}\n', file=open(path()))
        print(f'{dt.now()}: {message}\n')
        return
    print(f'{dt.now()}: Пользователь - {user.username}:{user.id}({user.first_name} {user.last_name}) *** {message}\n')
    print(f'{dt.now()}: Пользователь - {user.username}:{user.id}({user.first_name} {user.last_name}) *** {message}\n',
          file=open(path()))


def stop_writing_log():
    print(f'{dt.now()}: Завершение работы\n----------------\n')
    print(f'{dt.now()}: Завершение работы\n----------------\n',
          file=open(path('log.txt'), mode='a+', encoding='utf-8'))
