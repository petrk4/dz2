"""Операции со схемами таблиц."""

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
