# Primitive DB

Автор: Petr Kritsyn, группа M26-555.

Учебный Python-пакет с интерактивным интерфейсом командной строки.
Требования: Python 3.12+ и uv 0.5+.

## Установка и запуск

```powershell
uv sync
uv run project
```

Альтернативный запуск: `uv run python -m primitive_db.main`.
Программа выводит `DB project is running!` и запускает цикл команд:

- `help` — показать справку;
- `exit` — завершить программу.

Неизвестная команда выводит подсказку. Ctrl+C и конец ввода завершают программу.
Для ввода используется библиотека `prompt`.

## Проверка и сборка

```powershell
uv run ruff --version
uv run ruff check .
uv build
uvx twine check dist/*
```

## Установка собранного пакета

В PowerShell установите wheel текущей версии:

```powershell
uv tool install .\dist\primitive_db-0.1.0-py3-none-any.whl
project
```

Если команда недоступна в PATH, выполните `uv tool update-shell`
и откройте новый терминал. После пересборки для обновления используйте
`uv tool install --force .\dist\primitive_db-0.1.0-py3-none-any.whl`.

Активация окружения необязательна для `uv run`. В PowerShell:
`.\.venv\Scripts\Activate.ps1`; в bash на Linux/macOS:
`source .venv/bin/activate`.

Исходники находятся в `src/primitive_db`. Зависимости зафиксированы в `uv.lock`.
Окружение `.venv`, артефакты `dist` и кеши исключены из Git.
