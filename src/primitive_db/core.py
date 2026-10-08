"""Операции со схемами таблиц и записями."""

from primitive_db.utils import load_table_data

SUPPORTED_TYPES = {"int", "str", "bool"}


def create_table(metadata, table_name, columns):
    """Проверить схему и добавить таблицу, не меняя данные при ошибке."""
    if table_name in metadata:
        print(f'Ошибка: Таблица "{table_name}" уже существует.')
        return metadata
    if not table_name.isidentifier():
        print(f"Некорректное значение: {table_name}. Попробуйте снова.")
        return metadata

    schema = ["ID:int"]
    names = set()
    for column in columns:
        parts = column.split(":")
        if len(parts) != 2:
            print(f"Некорректное значение: {column}. Попробуйте снова.")
            return metadata
        name, data_type = parts
        if (
            not name.isidentifier()
            or name in names
            or data_type not in SUPPORTED_TYPES
            or (name == "ID" and data_type != "int")
        ):
            print(f"Некорректное значение: {column}. Попробуйте снова.")
            return metadata
        names.add(name)
        if name != "ID":
            schema.append(column)

    metadata[table_name] = schema
    print(
        f'Таблица "{table_name}" успешно создана со столбцами: '
        + ", ".join(schema)
    )
    return metadata


def drop_table(metadata, table_name):
    """Удалить схему существующей таблицы."""
    if table_name not in metadata:
        print(f'Ошибка: Таблица "{table_name}" не существует.')
        return metadata
    del metadata[table_name]
    print(f'Таблица "{table_name}" успешно удалена.')
    return metadata


def list_tables(metadata):
    """Вывести имена таблиц в алфавитном порядке."""
    if not metadata:
        print("Таблиц пока нет.")
    for table_name in sorted(metadata):
        print(f"- {table_name}")


def get_schema(metadata, table_name):
    if table_name not in metadata:
        raise ValueError(f'Таблица "{table_name}" не существует.')
    schema = dict(column.split(":") for column in metadata[table_name])
    if schema.get("ID") != "int" or any(
        kind not in SUPPORTED_TYPES for kind in schema.values()
    ):
        raise ValueError(f"Некорректная схема таблицы: {table_name}")
    return schema


def validate_values(schema, values, allow_id=True):
    """Проверять точные типы: bool не считается int."""
    types = {"int": int, "str": str, "bool": bool}
    for name, value in values.items():
        if name not in schema:
            raise ValueError(f"Столбец {name} не существует")
        if name == "ID" and not allow_id:
            raise ValueError("ID генерируется автоматически и не изменяется")
        if type(value) is not types[schema[name]]:
            raise ValueError(f"Столбец {name} требует тип {schema[name]}")


def validate_table_data(schema, table_data):
    ids = set()
    for row in table_data:
        if set(row) != set(schema):
            raise ValueError("Данные таблицы не соответствуют схеме")
        validate_values(schema, row)
        if row["ID"] < 1 or row["ID"] in ids:
            raise ValueError("Некорректный или повторяющийся ID в данных таблицы")
        ids.add(row["ID"])


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
    return [*table_data, {"ID": new_id, **record}]


def _matches(row, clause):
    return all(
        name in row and type(row[name]) is type(value) and row[name] == value
        for name, value in clause.items()
    )


def select(table_data, where_clause=None):
    return [row.copy() for row in table_data if _matches(row, where_clause or {})]


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
    return [
        {**row, **set_clause} if _matches(row, where_clause) else row.copy()
        for row in table_data
    ]


def delete(table_data, where_clause):
    if not where_clause:
        raise ValueError("Для delete требуется where")
    return [row.copy() for row in table_data if not _matches(row, where_clause)]
