"""Проверки схем и значений; ошибки обрабатываются на границе операций."""

from primitive_db.constants import ID_COLUMN, ID_TYPE, TYPE_MAP, VALID_TYPES


def get_schema(metadata, table_name):
    """Получить схему существующей таблицы и проверить её типы."""
    if table_name not in metadata:
        raise ValueError(f'Таблица "{table_name}" не существует.')
    schema = dict(column.split(":") for column in metadata[table_name])
    if schema.get(ID_COLUMN) != ID_TYPE or any(
        kind not in VALID_TYPES for kind in schema.values()
    ):
        raise ValueError(f"Некорректная схема таблицы: {table_name}")
    return schema


def validate_values(schema, values, allow_id=True):
    """Проверять точные типы: bool не считается int."""
    for name, value in values.items():
        if name not in schema:
            raise ValueError(f"Столбец {name} не существует")
        if name == ID_COLUMN and not allow_id:
            raise ValueError("ID генерируется автоматически и не изменяется")
        if type(value) is not TYPE_MAP[schema[name]]:
            raise ValueError(f"Столбец {name} требует тип {schema[name]}")


def validate_table_data(schema, table_data):
    """Проверить обязательные поля, типы и уникальность ID."""
    ids = set()
    for row in table_data:
        if set(row) != set(schema):
            raise ValueError("Данные таблицы не соответствуют схеме")
        validate_values(schema, row)
        if row[ID_COLUMN] < 1 or row[ID_COLUMN] in ids:
            raise ValueError("Некорректный или повторяющийся ID в данных таблицы")
        ids.add(row[ID_COLUMN])
