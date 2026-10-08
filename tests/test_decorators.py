"""Проверки обёрток, отмены операций и корректности кэша."""

import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import Mock, patch

from primitive_db import core
from primitive_db.decorators import (
    confirm_action,
    create_cacher,
    handle_db_errors,
    log_time,
)
from primitive_db.engine import run
from primitive_db.utils import (
    load_metadata,
    load_table_data,
    save_metadata,
    save_table_data,
)


class DecoratorTests(unittest.TestCase):
    def setUp(self):
        self.output = io.StringIO()
        capture = redirect_stdout(self.output)
        capture.__enter__()
        self.addCleanup(capture.__exit__, None, None, None)
        core._select_cache.clear()

    def test_error_categories_and_return_value(self):
        for error, message in (
            (KeyError("users"), "Таблица или столбец"),
            (ValueError("bad"), "Ошибка валидации"),
            (FileNotFoundError(), "Файл данных не найден"),
            (PermissionError("denied"), "Ошибка файловой операции"),
            (RuntimeError("unexpected"), "непредвиденная ошибка"),
        ):

            def operation():
                raise error

            self.assertIsNone(handle_db_errors(operation)())
            self.assertIn(message, self.output.getvalue())
        self.assertEqual(handle_db_errors(lambda x: x + 1)(4), 5)

    def test_wraps_and_timing(self):
        def operation(value):
            """Original documentation."""
            return value

        for decorator in (handle_db_errors, log_time, confirm_action("test")):
            wrapped = decorator(operation)
            self.assertEqual(wrapped.__name__, operation.__name__)
            self.assertEqual(wrapped.__doc__, operation.__doc__)
            self.assertIs(wrapped.__wrapped__, operation)
        with patch("primitive_db.decorators.time.monotonic", side_effect=[10, 10.125]):
            self.assertEqual(log_time(operation)(42), 42)
        self.assertIn(
            "Функция operation выполнилась за 0.125 секунд", self.output.getvalue()
        )

    def test_confirmation_only_y_executes(self):
        action = Mock(return_value=42)
        for answer in ("n", "", "yes", "Y", "anything"):
            with patch("builtins.input", return_value=answer):
                self.assertIsNone(confirm_action("test")(action)())
        for error in (EOFError, KeyboardInterrupt):
            with patch("builtins.input", side_effect=error):
                self.assertIsNone(confirm_action("test")(action)())
        action.assert_not_called()
        with patch("builtins.input", return_value="y"):
            self.assertEqual(confirm_action("test")(action)(), 42)
        action.assert_called_once()

    def test_closure_caches_falsey_values_and_keeps_instances_separate(self):
        cache = create_cacher()
        value = Mock(return_value=None)
        self.assertIsNone(cache("key", value))
        self.assertIsNone(cache("key", value))
        value.assert_called_once()
        create_cacher()("key", value)
        self.assertEqual(value.call_count, 2)
        cache.clear()
        cache("key", value)
        self.assertEqual(value.call_count, 3)

    def test_failed_computation_is_not_cached(self):
        cache = create_cacher()
        value = Mock(side_effect=[ValueError("bad"), 42])
        with self.assertRaises(ValueError):
            cache("key", value)
        self.assertEqual(cache("key", value), 42)

    def test_select_hits_cache_and_returns_independent_results(self):
        rows = [{"ID": 1, "age": 28}]
        with patch("primitive_db.core._matches", wraps=core._matches) as matches:
            result = core.select(rows, {"age": 28})
            result[0]["age"] = 999
            self.assertEqual(core.select(rows, {"age": 28})[0]["age"], 28)
            matches.assert_called_once()
            rows[0]["age"] = 29
            self.assertEqual(core.select(rows, {"age": 28}), [])
            self.assertEqual(matches.call_count, 2)
        self.assertEqual(core.select(rows, {"ID": True}), [])
        self.assertEqual(core.select(rows, {"ID": 1}), rows)

    def test_mutations_invalidate_cache(self):
        rows = [{"ID": 1, "age": 28}]
        with patch("primitive_db.core._matches", wraps=core._matches) as matches:
            core.select(rows)
            core.select(rows)
            self.assertEqual(matches.call_count, 1)
            updated = core.update(rows, {"age": 29}, {"ID": 1})
            matches.reset_mock()
            self.assertEqual(core.select(rows), rows)
            matches.assert_called_once()
            self.assertEqual(core.select(updated)[0]["age"], 29)
        with patch("builtins.input", return_value="y"):
            self.assertEqual(core.select(core.delete(updated, {"ID": 1})), [])

    def test_cancelled_deletions_do_not_save_or_claim_success(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / "db_meta.json"
            metadata = {"users": ["ID:int", "age:int"]}
            save_metadata(path, metadata)
            with patch("primitive_db.utils.DATA_DIR", root / "data"):
                save_table_data("users", [{"ID": 1, "age": 28}])
                commands = ["delete from users where ID=1", "drop_table users", "exit"]
                with (
                    patch("builtins.input", return_value="n"),
                    patch("primitive_db.engine.prompt.string", side_effect=commands),
                    patch("primitive_db.engine.save_table_data") as save_data,
                    patch("primitive_db.engine.save_metadata") as save_meta,
                ):
                    run(path)
                save_data.assert_not_called()
                save_meta.assert_not_called()
                self.assertEqual(load_metadata(path), metadata)
                self.assertEqual(load_table_data("users"), [{"ID": 1, "age": 28}])
        self.assertEqual(self.output.getvalue().count("Операция отменена."), 2)
        self.assertNotIn("успешно удалена", self.output.getvalue())


if __name__ == "__main__":
    unittest.main()
