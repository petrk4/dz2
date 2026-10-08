# Primitive DB

Автор: Petr Kritsyn, группа M26-555.

Учебная база данных: создание, просмотр списка и удаление схем таблиц.
Требования: Python 3.12+ и uv 0.5+.

## Установка и запуск

```powershell
uv sync
uv run database
```

Также доступны `uv run python -m primitive_db.main` и прежняя команда
`uv run project`. Ctrl+C, конец ввода и команда `exit` завершают программу.

## Управление таблицами

| Команда | Действие |
| --- | --- |
| `create_table <имя> <столбец:тип> ...` | Создать таблицу |
| `list_tables` | Показать таблицы по алфавиту |
| `drop_table <имя>` | Удалить таблицу |
| `help` | Показать справку |
| `exit` | Выйти |

Типы столбцов: `int`, `str`, `bool`. Имена таблиц и столбцов должны быть
идентификаторами: буквы, цифры и `_`, без цифры в начале. Регистр учитывается.
Столбцы не должны повторяться. `ID:int` автоматически добавляется первым;
явно указанный `ID:int` не дублируется. Другой тип для `ID` запрещён.
Можно создать таблицу только с автоматически добавленным ID.
На этом этапе хранятся схемы таблиц, операции со строками данных ещё не реализованы.

```text
>>>Введите команду: create_table users name:str age:int is_active:bool
Таблица "users" успешно создана со столбцами: ID:int, name:str, age:int, is_active:bool
>>>Введите команду: create_table users name:str
Ошибка: Таблица "users" уже существует.
>>>Введите команду: list_tables
- users
>>>Введите команду: drop_table users
Таблица "users" успешно удалена.
>>>Введите команду: drop_table products
Ошибка: Таблица "products" не существует.
>>>Введите команду: exit
```

Ошибочная команда или аргумент выводит сообщение и возвращает к вводу.
Аргументы разбираются через `shlex.split`, поэтому можно использовать кавычки.

## Хранение и архитектура

Метаданные сохраняются в `db_meta.json` в **текущей рабочей папке**.
Отсутствующий файл означает пустую БД. После успешного создания или удаления
изменения сохраняются; перед следующим запросом файл перечитывается.
Для доступа к той же БД запускайте программу из той же папки.
При повреждённом JSON программа сообщает об ошибке и завершает работу,
сохраняя файл для ручного исправления. Файл исключён из Git.

Пример JSON: `{"users": ["ID:int", "name:str", "age:int"]}`.

- `src/primitive_db/core.py` — операции над схемами таблиц;
- `src/primitive_db/engine.py` — цикл команд, справка и разбор ввода;
- `src/primitive_db/utils.py` — чтение и запись JSON;
- `src/primitive_db/main.py` — точка входа.

## Проверка и сборка

```powershell
uv run ruff check .
uv run python -m unittest discover -s tests -v
uv build
uvx twine check dist/*
```

## Установка собранного пакета

```powershell
uv tool install .\dist\primitive_db-0.2.0-py3-none-any.whl
database
```

Для обновления установленного инструмента добавьте `--force` к `uv tool install`.
Если команда недоступна в PATH, выполните `uv tool update-shell`
и откройте новый терминал.

Можно также установить wheel в отдельное окружение без установки исходников:

```powershell
uv venv build/demo-env
uv pip install --python build/demo-env/Scripts/python.exe .\dist\primitive_db-0.2.0-py3-none-any.whl
.\build\demo-env\Scripts\Activate.ps1
database
```

На Linux/macOS используйте `build/demo-env/bin/python` и
`source build/demo-env/bin/activate`.

## Демонстрация

[![Установка и управление таблицами](https://asciinema.org/a/8SslbIRRmHzrJXy6.svg)](https://asciinema.org/a/8SslbIRRmHzrJXy6)

[Запись установки и работы БД в формате asciicast](docs/database.cast).
Запись содержит реальный вывод установки wheel в отдельное окружение,
запуска `database`, создания, просмотра списка и удаления таблицы,
а также обработки повторного создания и удаления отсутствующей таблицы.

Воспроизведение и публикация через CLI asciinema:

```bash
asciinema play docs/database.cast
asciinema upload docs/database.cast
```

Копия записи в репозитории остаётся доступной независимо от внешнего сервиса.
