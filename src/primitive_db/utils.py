"""Чтение и сохранение метаданных."""

import json


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
    with open(filepath, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)
        file.write("\n")
