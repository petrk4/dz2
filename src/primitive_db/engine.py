"""Интерактивный цикл и разбор команд."""

import shlex

import prompt

from primitive_db.core import create_table, drop_table, list_tables
from primitive_db.utils import load_metadata, save_metadata

HELP = """\n***Процесс работы с таблицей***
Функции:
<command> create_table <имя_таблицы> <столбец1:тип> .. - создать таблицу
<command> list_tables - показать список всех таблиц
<command> drop_table <имя_таблицы> - удалить таблицу

Общие команды:
<command> exit - выход из программы
<command> help - справочная информация

Типы данных: int, str, bool. Столбец ID:int добавляется автоматически.
"""


def print_help():
    """Показать доступные команды."""
    print(HELP)


def run(filepath="db_meta.json"):
    """Запустить БД, перечитывая метаданные перед каждым запросом."""
    print("***База данных***")
    print_help()
    while True:
        try:
            metadata = load_metadata(filepath)
        except (OSError, ValueError) as error:
            print(f"Ошибка чтения метаданных: {error}")
            return

        try:
            user_input = prompt.string(">>>Введите команду: ")
        except (EOFError, KeyboardInterrupt):
            print()
            return
        try:
            args = shlex.split(user_input)
        except ValueError:
            print(f"Некорректное значение: {user_input}. Попробуйте снова.")
            continue
        if not args:
            continue

        command, *arguments = args
        if command not in {"create_table", "drop_table", "list_tables", "help", "exit"}:
            print(f"Функции {command} нет. Попробуйте снова.")
            continue
        if (
            (command == "create_table" and not arguments)
            or (command == "drop_table" and len(arguments) != 1)
            or (command in {"list_tables", "help", "exit"} and arguments)
        ):
            print(f"Некорректное значение: {user_input}. Попробуйте снова.")
            continue

        previous = metadata.copy()
        if command == "exit":
            return
        elif command == "help":
            print_help()
        elif command == "list_tables":
            list_tables(metadata)
        elif command == "create_table":
            create_table(metadata, arguments[0], arguments[1:])
        elif command == "drop_table":
            drop_table(metadata, arguments[0])

        if metadata != previous:
            try:
                save_metadata(filepath, metadata)
            except OSError as error:
                print(f"Ошибка сохранения метаданных: {error}")
                return
