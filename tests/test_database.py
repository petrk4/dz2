"""Проверки схем, сохранения и интерактивного цикла."""

import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from primitive_db.core import create_table, drop_table
from primitive_db.engine import run
from primitive_db.utils import load_metadata, save_metadata


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "db_meta.json"
        data_dir = patch("primitive_db.utils.DATA_DIR", Path(self.temp.name) / "data")
        data_dir.start()
        self.addCleanup(data_dir.stop)
        self.output = io.StringIO()
        self.capture = redirect_stdout(self.output)
        self.capture.__enter__()
        self.addCleanup(self.capture.__exit__, None, None, None)

    def session(self, commands):
        with patch("primitive_db.engine.prompt.string", side_effect=commands):
            run(self.path)

    def test_create_and_explicit_id(self):
        metadata = {}
        self.assertIs(create_table(metadata, "users", ["name:str"]), metadata)
        self.assertEqual(metadata["users"], ["ID:int", "name:str"])
        create_table(metadata, "explicit", ["name:str", "ID:int", "active:bool"])
        self.assertEqual(metadata["explicit"], ["ID:int", "name:str", "active:bool"])
        create_table(metadata, "only_id", [])
        self.assertEqual(metadata["only_id"], ["ID:int"])

    def test_invalid_columns_do_not_change_metadata(self):
        for columns in (
            ["good:str", "bad:float"], ["name"], ["a:int:bool"], [":str"],
            ["a:"], ["a:str", "a:int"], ["ID:str"], ["ID:int", "ID:int"],
            ["bad-name:int"],
        ):
            with self.subTest(columns=columns):
                metadata = {"existing": ["ID:int"]}
                create_table(metadata, "new", columns)
                self.assertEqual(metadata, {"existing": ["ID:int"]})
        metadata = {}
        create_table(metadata, "bad name", ["a:str"])
        self.assertEqual(metadata, {})

    def test_duplicate_and_drop(self):
        metadata = {"users": ["ID:int", "name:str"]}
        create_table(metadata, "users", ["age:int"])
        self.assertEqual(metadata["users"], ["ID:int", "name:str"])
        self.assertIs(drop_table(metadata, "absent"), metadata)
        self.assertIn("users", metadata)
        self.assertIs(drop_table(metadata, "users"), metadata)
        self.assertEqual(metadata, {})

    def test_json_round_trip(self):
        self.assertEqual(load_metadata(self.path), {})
        metadata = {"люди": ["ID:int", "имя:str"]}
        save_metadata(self.path, metadata)
        self.assertEqual(load_metadata(self.path), metadata)

    def test_persistence_between_sessions(self):
        self.session(["create_table users name:str age:int is_active:bool", "exit"])
        self.assertEqual(
            load_metadata(self.path)["users"],
            ["ID:int", "name:str", "age:int", "is_active:bool"],
        )
        self.session(["list_tables", "drop_table users", "list_tables", "exit"])
        self.assertIn("- users", self.output.getvalue())
        self.assertIn("Таблиц пока нет.", self.output.getvalue())
        self.assertEqual(load_metadata(self.path), {})

    def test_errors_reprompt_and_do_not_save(self):
        with patch("primitive_db.engine.save_metadata") as save:
            self.session([
                "nonsense", "create_table", "drop_table", "drop_table a b",
                "help extra", "list_tables extra", "exit extra", 'create_table "',
                "create_table users bad:float", "drop_table missing", "   ", "exit",
            ])
        save.assert_not_called()
        self.assertIn("Функции nonsense нет. Попробуйте снова.", self.output.getvalue())
        self.assertIn("Некорректное значение: bad:float.", self.output.getvalue())

    def test_shlex_and_help(self):
        self.session(['create_table "users" "name:str"', "help", "exit"])
        self.assertEqual(load_metadata(self.path), {"users": ["ID:int", "name:str"]})
        self.assertEqual(
            self.output.getvalue().count("***Процесс работы с таблицей***"), 2
        )

    def test_reload_before_each_prompt(self):
        def respond(_):
            save_metadata(self.path, {"external": ["ID:int"]})
            return "help"

        with patch("primitive_db.engine.prompt.string", side_effect=respond) as prompt:
            def commands(_):
                if prompt.call_count == 1:
                    return respond(_)
                if prompt.call_count == 2:
                    return "list_tables"
                return "exit"
            prompt.side_effect = commands
            run(self.path)
        self.assertIn("- external", self.output.getvalue())

    def test_corrupt_file_is_preserved(self):
        for content in ("{broken", "[]", '{"users": 1}'):
            self.path.write_text(content, encoding="utf-8")
            self.session([])
            self.assertEqual(self.path.read_text(encoding="utf-8"), content)
        self.assertIn("Ошибка чтения метаданных", self.output.getvalue())

    def test_input_interrupts(self):
        for interruption in (EOFError, KeyboardInterrupt):
            self.session([interruption])
        self.assertFalse(self.path.exists())

    def test_save_error_is_reported(self):
        with patch("primitive_db.engine.save_metadata", side_effect=OSError("denied")):
            self.session(["create_table users name:str"])
        self.assertIn("Ошибка сохранения метаданных: denied", self.output.getvalue())


if __name__ == "__main__":
    unittest.main()
