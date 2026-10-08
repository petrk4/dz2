"""Полные сеансы через стандартный ввод и вывод отдельного процесса."""

import os
import subprocess
import sys
import tempfile
import unittest


class ConsoleTests(unittest.TestCase):
    def test_complete_console_scenario_and_restart(self):
        with tempfile.TemporaryDirectory() as directory:

            def session(commands):
                result = subprocess.run(
                    [sys.executable, "-m", "primitive_db.main"],
                    input="\n".join([*commands, "exit", ""]),
                    cwd=directory,
                    env=dict(os.environ, PYTHONIOENCODING="utf-8"),
                    text=True,
                    encoding="utf-8",
                    capture_output=True,
                    timeout=15,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stderr, "")
                return result.stdout

            output = session(
                [
                    "create_table users name:str age:int is_active:bool",
                    'insert into users values ("Sergei", 28, true)',
                ]
            )
            self.assertIn("ID=1 успешно добавлена", output)
            output = session(
                [
                    "select from users where age = 28",
                    'update users set age = 29 where name = "Sergei"',
                    "select from users",
                    "delete from users where ID=1",
                    "n",
                    "info users",
                    "delete from users where ID=1",
                    "y",
                    "info users",
                    "drop_table users",
                    "y",
                    "list_tables",
                ]
            )
            for expected in (
                "Sergei",
                "29",
                "успешно обновлена",
                "Операция отменена",
                "Количество записей: 1",
                "Количество записей: 0",
                'Таблица "users" успешно удалена.',
                "Таблиц пока нет.",
            ):
                self.assertIn(expected, output)


if __name__ == "__main__":
    unittest.main()
