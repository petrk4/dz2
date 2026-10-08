"""Интерактивный цикл и разбор команд."""

import shlex

import prompt
from prettytable import PrettyTable

from primitive_db.constants import (
    DATA_COMMANDS,
    HELP,
    ID_COLUMN,
    INPUT_PROMPT,
    META_FILE,
    NO_ARGUMENT_COMMANDS,
    TABLE_COMMANDS,
)
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
    remove_table_data,
    save_metadata,
    save_table_data,
)
from primitive_db.validation import get_schema, validate_table_data, validate_values


def print_help():
    """Показать доступные команды."""
    print(HELP)


@handle_db_errors
def execute_data_command(metadata, text):
    """Выполнить CRUD-команду и сохранить только успешное изменение."""
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
            f"Запись с ID={data[-1][ID_COLUMN]} успешно добавлена "
            f'в таблицу "{table_name}".'
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
                    f'Запись с ID={row[ID_COLUMN]} в таблице "{table_name}" '
                    "успешно обновлена."
                )
            else:
                print(
                    f"Запись с ID={row[ID_COLUMN]} успешно удалена "
                    f'из таблицы "{table_name}".'
                )


@handle_db_errors
def execute_table_command(metadata, command, arguments, filepath):
    """Сообщить об успехе изменения таблицы только после сохранения файлов."""
    table_name = arguments[0]
    if command == "create_table":
        result = create_table(metadata, table_name, arguments[1:])
    else:
        result = drop_table(metadata, table_name)
    if result is None:
        return
    if command == "create_table":
        save_table_data(table_name, [])
    save_metadata(filepath, result)
    if command == "drop_table":
        remove_table_data(table_name)
        print(f'Таблица "{table_name}" успешно удалена.')
    else:
        print(
            f'Таблица "{table_name}" успешно создана со столбцами: '
            + ", ".join(result[table_name])
        )


def run(filepath=META_FILE):
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
            user_input = prompt.string(INPUT_PROMPT)
        except (EOFError, KeyboardInterrupt):
            print()
            return
        first_word = user_input.split(maxsplit=1)
        if first_word and first_word[0] in DATA_COMMANDS:
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
        if command not in TABLE_COMMANDS | NO_ARGUMENT_COMMANDS:
            print(f"Функции {command} нет. Попробуйте снова.")
            continue
        if (
            (command == "create_table" and not arguments)
            or (command == "drop_table" and len(arguments) != 1)
            or (command in NO_ARGUMENT_COMMANDS and arguments)
        ):
            print(f"Некорректное значение: {user_input}. Попробуйте снова.")
            continue

        if command == "exit":
            return
        elif command == "help":
            print_help()
        elif command == "list_tables":
            list_tables(metadata)
        else:
            execute_table_command(metadata, command, arguments, filepath)
