"""Разбор ограниченного SQL-синтаксиса с типизированными литералами."""

import ast
import re

TOKEN = re.compile(
    r'''\s*("(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|[+-]?\d+|[^\W\d]\w*|[(),=])'''
)


def tokenize(text):
    tokens = []
    position = 0
    text = text.strip()
    while position < len(text):
        match = TOKEN.match(text, position)
        if match is None:
            raise ValueError(f"Некорректное значение: {text[position:]}")
        tokens.append(match[1])
        position = match.end()
    return tokens


def parse_value(token):
    """Различать int, bool и строки, обязательно заключённые в кавычки."""
    if token.startswith(('"', "'")):
        try:
            value = ast.literal_eval(token)
        except (ValueError, SyntaxError) as error:
            raise ValueError(f"Некорректная строка: {token}") from error
        if isinstance(value, str):
            return value
    if token.lower() in {"true", "false"}:
        return token.lower() == "true"
    if re.fullmatch(r"[+-]?\d+", token):
        return int(token)
    raise ValueError(f"Некорректное значение: {token}. Строки нужны в кавычках")


def _assignments(tokens, multiple=False):
    result = {}
    while tokens:
        if len(tokens) < 3 or not tokens[0].isidentifier() or tokens[1] != "=":
            raise ValueError("Ожидается <столбец> = <значение>")
        name = tokens[0]
        if name in result:
            raise ValueError(f"Повторяющийся столбец: {name}")
        result[name] = parse_value(tokens[2])
        tokens = tokens[3:]
        if tokens:
            if not multiple or tokens[0] != "," or len(tokens) == 1:
                raise ValueError("Некорректное условие или присваивание")
            tokens = tokens[1:]
    if not result:
        raise ValueError("Не задано условие или присваивание")
    return result


def parse_where(text):
    return _assignments(tokenize(text))


def parse_set(text):
    return _assignments(tokenize(text), multiple=True)


def parse_command(text):
    """Вернуть команду, имя таблицы и разобранные значения/условия."""
    tokens = tokenize(text)
    match tokens:
        case ["insert", "into", table, "values", "(", *values, ")"]:
            parsed = []
            for index, token in enumerate(values):
                if index % 2:
                    if token != ",":
                        raise ValueError("Значения нужно разделять запятыми")
                else:
                    parsed.append(parse_value(token))
            if values and len(values) % 2 == 0:
                raise ValueError("После запятой требуется значение")
            return "insert", table, parsed, None
        case ["select", "from", table]:
            return "select", table, None, None
        case ["select" | "delete" as command, "from", table, "where", *condition]:
            return command, table, None, _assignments(condition)
        case ["update", table, "set", *rest]:
            boundary = next(
                (i for i in range(3, len(rest), 4) if rest[i] == "where"), None
            )
            if boundary is None:
                raise ValueError("Для update требуется where")
            return (
                "update", table, _assignments(rest[:boundary], multiple=True),
                _assignments(rest[boundary + 1:]),
            )
        case ["info", table]:
            return "info", table, None, None
        case _:
            raise ValueError("Некорректный синтаксис команды. Введите help")
