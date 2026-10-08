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

## Управление таблицами

`create_table` создаёт таблицу, `list_tables` выводит список, `drop_table` удаляет таблицу.

Типы: `int`, `str`, `bool`. Строки вводятся в кавычках, все поля обязательны.
ID назначается автоматически и при вставке не указывается.

## CRUD-операции

`insert` добавляет запись, `select` читает, `update` изменяет, `delete` удаляет.
`where` задаёт условие равенства, `info` показывает схему и число записей.
`help` выводит справку, `exit` завершает программу.

Пример полного сеанса:

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

Метаданные хранятся в `db_meta.json`, записи — в `data/` текущей папки.

## Декораторы и кэширование

Ошибки обрабатываются с выводом сообщения. Удаление требует ответа `y`;
любой другой ответ отменяет действие. Для `insert` и `select` измеряется время.
Повторные выборки кэшируются, при изменении данных кэш очищается.

## Проверка

```sh
make lint
make test
make check
```

## Демонстрация

Установка, полный цикл работы с таблицей, обработка ошибок и подтверждение удаления:

[![Работа с базой данных](https://asciinema.org/a/HSWCNigQNoDRUTH5.svg)](https://asciinema.org/a/HSWCNigQNoDRUTH5)
