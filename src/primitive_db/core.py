"""Операции со схемами таблиц и записями."""

import json

from primitive_db.constants import ID_COLUMN, ID_SCHEMA, VALID_TYPES
from primitive_db.decorators import (
    confirm_action,
    create_cacher,
    handle_db_errors,
    log_time,
)
from primitive_db.utils import load_table_data
from primitive_db.validation import (
    get_schema,
    validate_table_data,
    validate_values,
)

_select_cache = create_cacher()


@handle_db_errors
def create_table(metadata, table_name, columns):
    """Проверить схему и добавить таблицу, не меняя данные при ошибке."""
    if table_name in metadata:
        raise ValueError(f'Таблица "{table_name}" уже существует.')
    if not table_name.isidentifier():
        raise ValueError(f"Некорректное значение: {table_name}. Попробуйте снова.")

    schema = [ID_SCHEMA]
    names = set()
    for column in columns:
        parts = column.split(":")
        if len(parts) != 2:
            raise ValueError(f"Некорректное значение: {column}. Попробуйте снова.")
        name, data_type = parts
        if (
            not name.isidentifier()
            or name in names
            or data_type not in VALID_TYPES
            or (name == ID_COLUMN and data_type != "int")
        ):
            raise ValueError(f"Некорректное значение: {column}. Попробуйте снова.")
        names.add(name)
        if name != ID_COLUMN:
            schema.append(column)

    metadata[table_name] = schema
    _select_cache.clear()
    print(f'Таблица "{table_name}" успешно создана со столбцами: ' + ", ".join(schema))
    return metadata


@handle_db_errors
@confirm_action("удаление таблицы")
def drop_table(metadata, table_name):
    """Удалить схему существующей таблицы."""
    if table_name not in metadata:
        raise KeyError(table_name)
    del metadata[table_name]
    _select_cache.clear()
    print(f'Таблица "{table_name}" успешно удалена.')
    return metadata


@handle_db_errors
def list_tables(metadata):
    """Вывести имена таблиц в алфавитном порядке."""
    if not metadata:
        print("Таблиц пока нет.")
    for table_name in sorted(metadata):
        print(f"- {table_name}")


@handle_db_errors
@log_time
def insert(metadata, table_name, values, table_data=None):
    """Добавить запись с ID=max(IDs)+1, не меняя исходный список."""
    schema = get_schema(metadata, table_name)
    columns = [name for name in schema if name != "ID"]
    if len(values) != len(columns):
        raise ValueError(f"Ожидается значений: {len(columns)}, получено: {len(values)}")
    record = dict(zip(columns, values, strict=True))
    validate_values(schema, record, allow_id=False)
    if table_data is None:
        table_data = load_table_data(table_name)
    validate_table_data(schema, table_data)
    new_id = max((row["ID"] for row in table_data), default=0) + 1
    _select_cache.clear()
    return [*table_data, {"ID": new_id, **record}]


def _matches(row, clause):
    """Сравнить значения с учётом точного типа."""
    return all(
        name in row and type(row[name]) is type(value) and row[name] == value
        for name, value in clause.items()
    )


@handle_db_errors
@log_time
def select(table_data, where_clause=None):
    """Вернуть копии подходящих записей, кэшируя повторную фильтрацию."""
    # Снимок данных в ключе учитывает также изменения файла вне программы.
    key = json.dumps([table_data, where_clause or {}], sort_keys=True)
    result = _select_cache(
        key,
        lambda: [row.copy() for row in table_data if _matches(row, where_clause or {})],
    )
    return [row.copy() for row in result]


@handle_db_errors
def update(table_data, set_clause, where_clause):
    """Обновить все совпадения, сохранив исходные записи при ошибке."""
    if not set_clause or not where_clause:
        raise ValueError("Для update нужны set и where")
    if "ID" in set_clause:
        raise ValueError("ID генерируется автоматически и не изменяется")
    for row in table_data:
        for name, value in set_clause.items():
            if name not in row or type(value) is not type(row[name]):
                raise ValueError(f"Некорректное значение столбца: {name}")
    result = [
        {**row, **set_clause} if _matches(row, where_clause) else row.copy()
        for row in table_data
    ]
    _select_cache.clear()
    return result


@handle_db_errors
@confirm_action("удаление записей")
def delete(table_data, where_clause):
    """Удалить все совпадения после подтверждения пользователя."""
    if not where_clause:
        raise ValueError("Для delete требуется where")
    result = [row.copy() for row in table_data if not _matches(row, where_clause)]
    _select_cache.clear()
    return result
