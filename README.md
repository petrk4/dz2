# Primitive DB

Консольная база данных на Python. Таблицы и записи хранятся в JSON.

Petr Kritsyn, M26-555.

## Запуск

Нужны Python 3.12+, uv и GNU Make.

```sh
make install
make run
```

Без Make: `uv sync`, затем `uv run database`.

## Команды

```text
create_table users name:str age:int is_active:bool
list_tables
insert into users values ("Sergei", 28, true)
select from users
select from users where age = 28
update users set age = 29 where name = "Sergei"
info users
delete from users where ID = 1
y
drop_table users
y
help
exit
```

Типы: `int`, `str`, `bool`. Строки вводятся в кавычках, все поля обязательны.
ID назначается автоматически. Удаление требует ответа `y`.
Метаданные хранятся в `db_meta.json`, записи — в `data/` текущей папки.
Ошибки выводятся в консоль. Для `insert` и `select` измеряется время;
результаты повторных выборок кэшируются.

## Проверка

```sh
make lint
make test
make check
```

## Демонстрация

[![Работа с базой данных](https://asciinema.org/a/HSWCNigQNoDRUTH5.svg)](https://asciinema.org/a/HSWCNigQNoDRUTH5)
