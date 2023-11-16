import os

from telebot.types import *
from datetime import datetime as dt
from pathlib import Path


DIR_PATH = Path.cwd()


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
