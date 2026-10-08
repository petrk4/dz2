"""Чтение и атомарное сохранение JSON-файлов."""

import json
import os

from primitive_db.constants import DATA_DIR, ENCODING, JSON_INDENT, TEMP_TOKEN_BYTES


def load_metadata(filepath):
    """Прочитать метаданные; отсутствие файла означает пустую базу."""
    try:
        with open(filepath, encoding=ENCODING) as file:
            data = json.load(file)
    except FileNotFoundError:
        return {}
    if not isinstance(data, dict) or not all(
        isinstance(name, str)
        and isinstance(columns, list)
        and all(isinstance(column, str) for column in columns)
        for name, columns in data.items()
    ):
        raise ValueError("Некорректная структура метаданных")
    return data


def save_metadata(filepath, data):
    """Сохранить метаданные в JSON с читаемым русским текстом."""
    _save_json(filepath, data)


def _save_json(filepath, data):
    """Заменить JSON только после успешной записи временного файла."""
    directory = os.path.dirname(os.path.abspath(filepath))
    temporary = os.path.join(directory, f".db-{os.urandom(TEMP_TOKEN_BYTES).hex()}.tmp")
    created = False
    try:
        with open(temporary, "x", encoding=ENCODING) as file:
            created = True
            json.dump(data, file, ensure_ascii=False, indent=JSON_INDENT)
            file.write("\n")
        os.replace(temporary, filepath)
    finally:
        if created and os.path.exists(temporary):
            os.remove(temporary)


def table_path(table_name):
    """Получить путь внутри data, запретив пути вместо имён таблиц."""
    if not table_name.isidentifier():
        raise ValueError(f"Некорректное имя таблицы: {table_name}")
    return os.path.join(DATA_DIR, f"{table_name}.json")


def load_table_data(table_name):
    """Прочитать записи таблицы; отсутствующий файл означает пустой список."""
    try:
        with open(table_path(table_name), encoding=ENCODING) as file:
            data = json.load(file)
    except FileNotFoundError:
        return []
    if not isinstance(data, list) or not all(isinstance(row, dict) for row in data):
        raise ValueError(f"Некорректные данные таблицы: {table_name}")
    return data


def save_table_data(table_name, data):
    """Сохранить записи в отдельный JSON-файл."""
    filepath = table_path(table_name)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    _save_json(filepath, data)


def remove_table_data(table_name):
    """Удалить файл таблицы, если он существует."""
    try:
        os.remove(table_path(table_name))
    except FileNotFoundError:
        pass
