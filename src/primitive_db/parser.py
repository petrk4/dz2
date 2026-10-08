"""Разбор ограниченного SQL-синтаксиса без выполнения введённого кода."""

import json

from primitive_db.constants import BOOL_LITERALS


def tokenize(text):
    """Выделить слова, числа, пунктуацию и строки, сохраняя кавычки."""
    tokens = []
    position = 0
    while position < len(text):
        char = text[position]
        if char.isspace():
            position += 1
            continue
        start = position
        position += 1
        if char in "\"'":
            while position < len(text):
                if text[position] == "\\":
                    position += 2
                elif text[position] == char:
                    position += 1
                    break
                else:
                    position += 1
            else:
                raise ValueError("Незакрытые кавычки")
        elif char in "(),=":
            pass
        elif char.isalnum() or char in "_+-":
            while position < len(text) and (
                text[position].isalnum() or text[position] == "_"
            ):
                position += 1
        else:
            raise ValueError(f"Некорректное значение: {text[start:]}")
        tokens.append(text[start:position])
    return tokens


def parse_value(token):
    """Различать целые числа, bool и строки в кавычках."""
    if token.startswith('"'):
        return json.loads(token)
    if token.startswith("'") and token.endswith("'"):
        # Преобразовать одиночные кавычки в JSON, сохранив escape-последовательности.
        body = token[1:-1]
        encoded = []
        position = 0
        while position < len(body):
            char = body[position]
            if char == "\\" and position + 1 < len(body):
                following = body[position + 1]
                encoded.append("'" if following == "'" else "\\" + following)
                position += 2
            else:
                encoded.append('\\"' if char == '"' else char)
                position += 1
        return json.loads('"' + "".join(encoded) + '"')
    if token.lower() in BOOL_LITERALS:
        return BOOL_LITERALS[token.lower()]
    digits = token[1:] if token.startswith(("+", "-")) else token
    if digits and digits.isdecimal():
        return int(token)
    raise ValueError(f"Некорректное значение: {token}. Строки нужны в кавычках")


def _assignments(tokens, multiple=False):
    """Разобрать одно равенство или список присваиваний через запятую."""
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
    """Преобразовать условие равенства в словарь."""
    return _assignments(tokenize(text))


def parse_set(text):
    """Преобразовать присваивания столбцам в словарь."""
    return _assignments(tokenize(text), multiple=True)


def parse_values(tokens):
    """Разобрать значения между скобками, разделённые запятыми."""
    parsed = []
    expect_value = True
    for token in tokens:
        if expect_value:
            parsed.append(parse_value(token))
        elif token != ",":
            raise ValueError("Значения нужно разделять запятыми")
        expect_value = not expect_value
    if tokens and expect_value:
        raise ValueError("После запятой требуется значение")
    return parsed


def parse_command(text):
    """Вернуть команду, имя таблицы и разобранные значения/условия."""
    tokens = tokenize(text)
    match tokens:
        case ["insert", "into", table, "values", "(", *values, ")"]:
            return "insert", table, parse_values(values), None
        case ["select", "from", table]:
            return "select", table, None, None
        case ["select" | "delete" as command, "from", table, "where", *condition]:
            return command, table, None, _assignments(condition)
        case ["update", table, "set", *rest]:
            # Присваивание занимает три токена, затем запятая либо where.
            boundary = next(
                (i for i in range(3, len(rest), 4) if rest[i] == "where"), None
            )
            if boundary is None:
                raise ValueError("Для update требуется where")
            return (
                "update",
                table,
                _assignments(rest[:boundary], multiple=True),
                _assignments(rest[boundary + 1 :]),
            )
        case ["info", table]:
            return "info", table, None, None
        case _:
            raise ValueError("Некорректный синтаксис команды. Введите help")
