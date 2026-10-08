"""Общие настройки хранения, типов и интерфейса базы данных."""

META_FILE = "db_meta.json"
DATA_DIR = "data"
ENCODING = "utf-8"
JSON_INDENT = 2
TEMP_TOKEN_BYTES = 16
ID_COLUMN = "ID"
ID_TYPE = "int"
ID_SCHEMA = f"{ID_COLUMN}:{ID_TYPE}"
VALID_TYPES = {"int", "str", "bool"}
TYPE_MAP = {"int": int, "str": str, "bool": bool}
BOOL_LITERALS = {"true": True, "false": False}
CONFIRM_RESPONSE = "y"
INPUT_PROMPT = ">>>Введите команду: "
DATA_COMMANDS = {"insert", "select", "update", "delete", "info"}
TABLE_COMMANDS = {"create_table", "drop_table"}
NO_ARGUMENT_COMMANDS = {"list_tables", "help", "exit"}

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
