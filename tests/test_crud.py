"""CRUD: типы, парсер, файловое хранение и ошибки без потери данных."""

import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from primitive_db.core import delete, insert, select, update
from primitive_db.engine import run
from primitive_db.parser import parse_command, parse_set, parse_where
from primitive_db.utils import load_table_data, save_metadata, save_table_data


class CrudTests(unittest.TestCase):
    def setUp(self):
        confirmation = patch("builtins.input", return_value="y")
        confirmation.start()
        self.addCleanup(confirmation.stop)
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.meta_path = self.root / "db_meta.json"
        self.data_path = self.root / "data" / "users.json"
        data_dir = patch("primitive_db.utils.DATA_DIR", self.root / "data")
        data_dir.start()
        self.addCleanup(data_dir.stop)
        self.metadata = {"users": ["ID:int", "name:str", "age:int", "active:bool"]}
        save_metadata(self.meta_path, self.metadata)

    def session(self, commands):
        output = io.StringIO()
        with redirect_stdout(output):
            with patch("primitive_db.engine.prompt.string", side_effect=commands):
                run(self.meta_path)
        return output.getvalue()

    def test_insert_persistence_and_id_after_gap(self):
        rows = insert(self.metadata, "users", ["Sergei", 28, True])
        save_table_data("users", rows)
        rows = insert(self.metadata, "users", ["Anna", 30, False])
        rows = insert(self.metadata, "users", ["Max", 31, True], rows)
        rows = delete(rows, {"ID": 2})
        save_table_data("users", rows)
        rows = insert(self.metadata, "users", ["Next", 32, False])
        self.assertEqual([row["ID"] for row in rows], [1, 3, 4])

    def test_insert_rejects_wrong_count_and_types(self):
        for values in (
            [], [1, "Sergei", 28, True], ["Sergei", "28", True],
            ["Sergei", True, True], ["Sergei", 28, 1], [None, 28, True],
        ):
            with self.subTest(values=values):
                self.assertIsNone(insert(self.metadata, "users", values))
        self.assertIsNone(insert(self.metadata, "missing", []))
        self.assertFalse(self.data_path.exists())

    def test_select_update_delete_multiple_matches(self):
        rows = [
            {"ID": 1, "name": "A", "age": 28, "active": True},
            {"ID": 2, "name": "B", "age": 28, "active": False},
            {"ID": 3, "name": "C", "age": 30, "active": True},
        ]
        self.assertEqual(len(select(rows)), 3)
        self.assertEqual(len(select(rows, {"age": 28})), 2)
        self.assertEqual(select(rows, {"ID": True}), [])
        updated = update(rows, {"age": 29}, {"age": 28})
        self.assertEqual([row["age"] for row in updated], [29, 29, 30])
        self.assertEqual(rows[0]["age"], 28)
        self.assertEqual(delete(updated, {"age": 29}), [rows[2]])
        for changes in ({"ID": 4}, {"missing": 1}, {"age": False}):
            self.assertIsNone(update(rows, changes, {"ID": 1}))

    def test_full_cli_across_sessions(self):
        output = self.session(['insert into users values ("Sergei",28,true)', "exit"])
        self.assertIn("Запись с ID=1 успешно добавлена", output)
        output = self.session([
            "select from users where age=28",
            'update users set age=29,active=false where name="Sergei"',
            "info users", "exit",
        ])
        self.assertIn("|", output)
        self.assertIn("Sergei", output)
        self.assertIn("успешно обновлена", output)
        self.assertIn("Количество записей: 1", output)
        self.assertEqual(load_table_data("users")[0]["age"], 29)
        self.assertIs(load_table_data("users")[0]["active"], False)
        output = self.session(["delete from users where ID=1", "info users", "exit"])
        self.assertIn("успешно удалена", output)
        self.assertIn("Количество записей: 0", output)
        self.assertEqual(load_table_data("users"), [])

    def test_invalid_commands_preserve_data(self):
        save_table_data("users", insert(self.metadata, "users", ["A", 28, True]))
        before = self.data_path.read_bytes()
        output = self.session([
            'insert into users values ("A",true,true)',
            'update users set age="wrong" where ID=1',
            "update users set ID=2 where ID=1",
            "update users set age=2", "delete from users",
            "select from users where missing=1", "select from users where age=true",
            "delete from users where ID=true", 'insert into missing values ("A")',
            'insert into users values ("unfinished)', "info missing", "exit",
        ])
        self.assertEqual(output.count("Ошибка"), 11)
        self.assertEqual(self.data_path.read_bytes(), before)

    def test_drop_and_recreate_clears_data(self):
        save_table_data("users", insert(self.metadata, "users", ["A", 28, True]))
        self.session(["drop_table users", "exit"])
        self.assertFalse(self.data_path.exists())
        self.session(["create_table users name:str", 'insert into users values ("B")',
                      "exit"])
        self.assertEqual(load_table_data("users"), [{"ID": 1, "name": "B"}])

    def test_corrupt_data_is_not_overwritten(self):
        self.data_path.parent.mkdir()
        for text in ("{broken", "{}", '[{"ID":1}]'):
            self.data_path.write_text(text, encoding="utf-8")
            output = self.session(['insert into users values ("A",1,true)', "exit"])
            self.assertIn("Ошибка", output)
            self.assertEqual(self.data_path.read_text(encoding="utf-8"), text)

    def test_failed_write_preserves_existing_file(self):
        save_table_data("users", [])
        before = self.data_path.read_bytes()
        with patch("primitive_db.utils.os.replace", side_effect=OSError("denied")):
            output = self.session(['insert into users values ("A",1,true)', "exit"])
        self.assertIn("denied", output)
        self.assertNotIn("успешно добавлена", output)
        self.assertEqual(self.data_path.read_bytes(), before)

    def test_no_matches_and_empty_table(self):
        output = self.session(["select from users", "update users set age=4 where ID=1",
                               "delete from users where ID=1", "info users", "exit"])
        self.assertEqual(output.count("Подходящих записей нет."), 2)
        self.assertIn("Количество записей: 0", output)
        self.assertFalse(self.data_path.exists())


class ParserTests(unittest.TestCase):
    def test_literals_and_delimiters_inside_strings(self):
        command = 'insert into users values ("A, where = (B)", -12, false)'
        self.assertEqual(parse_command(command)[2], ["A, where = (B)", -12, False])
        self.assertEqual(parse_where('name="two words"'), {"name": "two words"})
        self.assertEqual(parse_set('age=29, name=""'), {"age": 29, "name": ""})
        self.assertEqual(parse_where(r"name='O\'Brien'"), {"name": "O'Brien"})
        self.assertEqual(parse_command("update t set where=2 where ID=1")[2],
                         {"where": 2})

    def test_rejects_bad_syntax(self):
        for text in (
            'insert into t values ("a",)', 'insert into t values ("a" "b")',
            "insert into t values (bare)", "insert into t values (null)",
            "insert into t values (1.5)", "delete from t", "select from t where",
            "update t set age=1", "update t set age=1,age=2 where ID=1",
            "select from t where age==1", "info t extra", "select from t;",
        ):
            with self.subTest(text=text), self.assertRaises(ValueError):
                parse_command(text)


if __name__ == "__main__":
    unittest.main()
