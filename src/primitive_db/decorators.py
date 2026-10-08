"""Общие обёртки операций и кэш на основе замыкания."""

import time
from functools import wraps


def handle_db_errors(func):
    """Сообщить об ошибке; None означает, что операция не выполнена."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except FileNotFoundError:
            print(
                "Ошибка: Файл данных не найден. "
                "Возможно, база данных не инициализирована."
            )
        except KeyError as error:
            print(f"Ошибка: Таблица или столбец {error} не найден.")
        except ValueError as error:
            print(f"Ошибка валидации: {error}")
        except OSError as error:
            print(f"Ошибка файловой операции: {error}")
        except Exception as error:
            print(f"Произошла непредвиденная ошибка: {error}")
        return None

    return wrapper


def confirm_action(action_name):
    """Выполнить действие только при ответе y; иначе вернуть None."""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                answer = input(
                    f'Вы уверены, что хотите выполнить "{action_name}"? [y/n]: '
                )
            except (EOFError, KeyboardInterrupt):
                print()
                answer = ""
            if answer.strip() != "y":
                print("Операция отменена.")
                return None
            return func(*args, **kwargs)

        return wrapper

    return decorator


def log_time(func):
    """Измерить полное время вызова, сохранив результат и исключения."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        started = time.monotonic()
        try:
            return func(*args, **kwargs)
        finally:
            elapsed = time.monotonic() - started
            print(f"Функция {func.__name__} выполнилась за {elapsed:.3f} секунд")

    return wrapper


def create_cacher():
    """Создать независимый кэш; clear() очищает сохранённые результаты."""
    cache = {}

    def cache_result(key, value_func):
        if key not in cache:
            cache[key] = value_func()
        return cache[key]

    cache_result.clear = cache.clear
    return cache_result
