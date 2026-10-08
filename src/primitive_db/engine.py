"""Интерактивный цикл и разбор команд."""

import shlex

import prompt
from prettytable import PrettyTable

from primitive_db.core import (
    create_table,
    delete,
    drop_table,
    insert,
    list_tables,
    select,
    update,
)
from primitive_db.decorators import handle_db_errors
from primitive_db.parser import parse_command
from primitive_db.utils import (
    load_metadata,
    load_table_data,
    save_metadata,
    save_table_data,
    table_path,
)
from primitive_db.validation import get_schema, validate_table_data, validate_values

HELP = """\n***Процесс работы с таблицей***
Функции:
<command> create_table <имя_таблицы> <столбец1:тип> .. - создать таблицу
<command> list_tables - показать список всех таблиц
<command> drop_table <имя_таблицы> - удалить таблицу

***Операции с данными***
insert into <таблица> values (<значение1>, <значение2>, ...) - создать запись
select from <таблица> [where <столбец> = <значение>] - прочитать записи
update <таблица> set <столбец> = <значение> where <столбец> = <значение>
delete from <таблица> where <столбец> = <значение> - удалить записи
info <таблица> - информация о таблице

Общие команды:
<command> exit - выход из программы
<command> help - справочная информация

Типы данных: int, str, bool. Столбец ID:int добавляется автоматически.
Строки в кавычках, bool: true/false. При insert значения ID не передаются.
Удаление таблиц и записей требует подтверждения y.
"""


def print_help():
    """Показать доступные команды."""
    print(HELP)


@handle_db_errors
def execute_data_command(metadata, text):
    command, table_name, values, where = parse_command(text)
    schema = get_schema(metadata, table_name)
    table_data = load_table_data(table_name)
    validate_table_data(schema, table_data)
    if where is not None:
        validate_values(schema, where)

    if command == "info":
        print(f"Таблица: {table_name}")
        print("Столбцы: " + ", ".join(metadata[table_name]))
        print(f"Количество записей: {len(table_data)}")
    elif command == "select":
        result = PrettyTable(list(schema))
        rows = select(table_data, where)
        if rows is None:
            return
        for row in rows:
            result.add_row([row[column] for column in schema])
        print(result)
    elif command == "insert":
        data = insert(metadata, table_name, values, table_data)
        if data is None:
            return
        save_table_data(table_name, data)
        print(
            f'Запись с ID={data[-1]["ID"]} успешно добавлена в таблицу "{table_name}".'
        )
    else:
        if command == "update":
            validate_values(schema, values, allow_id=False)
        matches = select(table_data, where)
        if matches is None:
            return
        if not matches:
            print("Подходящих записей нет.")
            return
        if command == "update":
            data = update(table_data, values, where)
        else:
            data = delete(table_data, where)
        if data is None:
            return
        save_table_data(table_name, data)
        for row in matches:
            if command == "update":
                print(
                    f'Запись с ID={row["ID"]} в таблице "{table_name}" '
                    "успешно обновлена."
                )
            else:
                print(
                    f"Запись с ID={row['ID']} успешно удалена "
                    f'из таблицы "{table_name}".'
                )


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
        first_word = user_input.split(maxsplit=1)
        if first_word and first_word[0] in {
            "insert",
            "select",
            "update",
            "delete",
            "info",
        }:
            execute_data_command(metadata, user_input)
            continue
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
                if command == "create_table":
                    save_table_data(arguments[0], [])
                save_metadata(filepath, metadata)
                if command == "drop_table":
                    table_path(arguments[0]).unlink(missing_ok=True)
            except OSError as error:
                print(f"Ошибка сохранения метаданных: {error}")
                return
