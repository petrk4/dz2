"""Чтение и сохранение метаданных."""

import json
import os
import tempfile
from pathlib import Path

DATA_DIR = Path("data")


def load_metadata(filepath):
    """Прочитать JSON; отсутствие файла означает пустую базу."""
    try:
        with open(filepath, encoding="utf-8") as file:
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
    _save_json(Path(filepath), data)


def _save_json(filepath, data):
    """Заменить JSON только после успешной записи временного файла."""
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=filepath.parent, delete=False
        ) as file:
            temporary = Path(file.name)
            json.dump(data, file, ensure_ascii=False, indent=2)
            file.write("\n")
        os.replace(temporary, filepath)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def table_path(table_name):
    """Получить путь внутри data, запретив пути вместо имён таблиц."""
    if not table_name.isidentifier():
        raise ValueError(f"Некорректное имя таблицы: {table_name}")
    return DATA_DIR / f"{table_name}.json"


def load_table_data(table_name):
    """Прочитать записи таблицы; отсутствующий файл означает пустой список."""
    try:
        with table_path(table_name).open(encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError:
        return []
    if not isinstance(data, list) or not all(isinstance(row, dict) for row in data):
        raise ValueError(f"Некорректные данные таблицы: {table_name}")
    return data


def save_table_data(table_name, data):
    """Сохранить записи в отдельный JSON-файл."""
    filepath = table_path(table_name)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    _save_json(filepath, data)
