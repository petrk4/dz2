"""Общие обёртки операций и кэш на основе замыкания."""

import time

from primitive_db.constants import CONFIRM_RESPONSE


def _preserve_metadata(func):
    """Сохранить атрибуты исходной функции без дополнительных библиотек."""

    def decorate(wrapper):
        """Перенести имя, документацию и ссылку на исходную функцию."""
        for attribute in (
            "__name__",
            "__qualname__",
            "__doc__",
            "__module__",
            "__annotations__",
        ):
            if hasattr(func, attribute):
                setattr(wrapper, attribute, getattr(func, attribute))
        wrapper.__dict__.update(func.__dict__)
        wrapper.__wrapped__ = func
        return wrapper

    return decorate


def handle_db_errors(func):
    """Сообщить об ошибке; None означает, что операция не выполнена."""

    @_preserve_metadata(func)
    def wrapper(*args, **kwargs):
        """Выполнить операцию и преобразовать исключение в сообщение."""
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
        """Обернуть указанную функцию запросом подтверждения."""

        @_preserve_metadata(func)
        def wrapper(*args, **kwargs):
            """Запросить подтверждение перед вызовом функции."""
            try:
                answer = input(
                    f'Вы уверены, что хотите выполнить "{action_name}"? [y/n]: '
                )
            except (EOFError, KeyboardInterrupt):
                print()
                answer = ""
            if answer.strip() != CONFIRM_RESPONSE:
                print("Операция отменена.")
                return None
            return func(*args, **kwargs)

        return wrapper

    return decorator


def log_time(func):
    """Измерить полное время вызова, сохранив результат и исключения."""

    @_preserve_metadata(func)
    def wrapper(*args, **kwargs):
        """Измерить вызов даже при исключении."""
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
        """Вычислить значение один раз для каждого ключа."""
        if key not in cache:
            cache[key] = value_func()
        return cache[key]

    cache_result.clear = cache.clear
    return cache_result
