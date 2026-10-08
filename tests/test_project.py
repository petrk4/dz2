"""Проверка ограничений на исходники установленного приложения."""

import ast
import unittest
from pathlib import Path


class ProjectChecks(unittest.TestCase):
    def test_source_restrictions(self):
        package = Path(__file__).resolve().parents[1] / "src" / "primitive_db"
        allowed = {
            "json",
            "shlex",
            "time",
            "os",
            "prettytable",
            "prompt",
            "primitive_db",
        }
        for source in package.glob("*.py"):
            tree = ast.parse(source.read_text(encoding="utf-8-sig"))
            for node in ast.walk(tree):
                with self.subTest(file=source.name, line=getattr(node, "lineno", 0)):
                    self.assertNotIsInstance(node, ast.ClassDef)
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        self.assertTrue(ast.get_docstring(node))
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            self.assertIn(alias.name.split(".")[0], allowed)
                    elif isinstance(node, ast.ImportFrom):
                        self.assertIn(node.module.split(".")[0], allowed)


if __name__ == "__main__":
    unittest.main()
