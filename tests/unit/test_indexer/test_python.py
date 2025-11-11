"""Tests for Python indexer.

Test coverage target: 85%
"""

import tempfile
from pathlib import Path

import pytest

from maze.indexer.languages.python import PythonIndexer


class TestPythonIndexer:
    """Tests for PythonIndexer."""

    def test_initialization(self):
        """Test indexer initialization."""
        indexer = PythonIndexer()
        assert indexer.language == "python"
        assert ".py" in indexer.file_extensions
        assert ".pyi" in indexer.file_extensions

    def test_index_simple_function(self):
        """Test indexing simple function."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.py"
            file_path.write_text("""
def add(x: int, y: int) -> int:
    return x + y
""")

            indexer = PythonIndexer()
            result = indexer.index_file(file_path)

            assert len(result.symbols) == 1
            symbol = result.symbols[0]
            assert symbol.name == "add"
            assert symbol.kind == "function"
            assert "int" in symbol.type_str

    def test_index_async_function(self):
        """Test indexing async function."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.py"
            file_path.write_text("""
async def fetch(url: str) -> dict:
    return {}
""")

            indexer = PythonIndexer()
            result = indexer.index_file(file_path)

            assert len(result.symbols) == 1
            symbol = result.symbols[0]
            assert symbol.name == "fetch"
            assert symbol.kind == "async_function"
            assert symbol.metadata["is_async"] is True

    def test_index_class(self):
        """Test indexing class definition."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.py"
            file_path.write_text("""
class User:
    '''User model.'''
    def __init__(self, name: str):
        self.name = name
""")

            indexer = PythonIndexer()
            result = indexer.index_file(file_path)

            # Should find class and __init__ method
            class_symbols = [s for s in result.symbols if s.kind == "class"]
            assert len(class_symbols) == 1
            assert class_symbols[0].name == "User"
            assert class_symbols[0].docstring == "User model."

    def test_index_dataclass(self):
        """Test indexing dataclass."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.py"
            file_path.write_text("""
from dataclasses import dataclass

@dataclass
class Point:
    x: float
    y: float
""")

            indexer = PythonIndexer()
            result = indexer.index_file(file_path)

            class_symbol = next(s for s in result.symbols if s.kind == "class")
            assert class_symbol.metadata["is_dataclass"] is True

    def test_index_typed_variable(self):
        """Test indexing variable with type annotation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.py"
            file_path.write_text("""
x: int = 42
users: list[str] = []
""")

            indexer = PythonIndexer()
            result = indexer.index_file(file_path)

            var_symbols = [s for s in result.symbols if s.kind == "variable"]
            assert len(var_symbols) == 2
            assert var_symbols[0].name == "x"
            assert var_symbols[0].type_str == "int"
            assert var_symbols[1].name == "users"
            assert "list" in var_symbols[1].type_str

    def test_index_imports(self):
        """Test extracting imports."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.py"
            file_path.write_text("""
import os
from pathlib import Path
from typing import Optional, List
""")

            indexer = PythonIndexer()
            result = indexer.index_file(file_path)

            assert len(result.imports) == 3
            assert result.imports[0].module == "os"
            assert result.imports[1].module == "pathlib"
            assert "Path" in result.imports[1].symbols
            assert result.imports[2].module == "typing"
            assert "Optional" in result.imports[2].symbols

    def test_detect_pytest_tests(self):
        """Test detecting pytest test functions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test_example.py"
            file_path.write_text("""
def test_addition():
    assert 1 + 1 == 2

def test_subtraction():
    assert 2 - 1 == 1
""")

            indexer = PythonIndexer()
            result = indexer.index_file(file_path)

            assert len(result.tests) == 2
            assert result.tests[0].name == "test_addition"
            assert "pytest" in result.tests[0].command

    def test_detect_unittest_tests(self):
        """Test detecting unittest test cases."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.py"
            file_path.write_text("""
import unittest

class TestMath(unittest.TestCase):
    def test_add(self):
        self.assertEqual(1 + 1, 2)
""")

            indexer = PythonIndexer()
            result = indexer.index_file(file_path)

            assert len(result.tests) >= 1
            test = result.tests[0]
            assert "TestMath" in test.name
            assert "test_add" in test.name

    def test_style_detection(self):
        """Test code style detection."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.py"
            file_path.write_text("""
def example():
    x = 'single quotes'
    return x
""")

            indexer = PythonIndexer()
            result = indexer.index_file(file_path)

            assert result.style.indent_size == 4
            assert result.style.indent_type == "space"
            assert result.style.quotes in ["single", "double"]
            assert result.style.semicolons is False

    def test_type_hint_union(self):
        """Test parsing union type hints."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.py"
            file_path.write_text("""
def func(x: int | str) -> bool:
    return True
""")

            indexer = PythonIndexer()
            result = indexer.index_file(file_path)

            symbol = result.symbols[0]
            assert "|" in symbol.type_str or "Union" in symbol.type_str

    def test_type_hint_generic(self):
        """Test parsing generic type hints."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.py"
            file_path.write_text("""
def process(items: list[int]) -> dict[str, int]:
    return {}
""")

            indexer = PythonIndexer()
            result = indexer.index_file(file_path)

            symbol = result.symbols[0]
            assert "list" in symbol.type_str or "dict" in symbol.type_str

    def test_index_directory(self):
        """Test indexing directory of Python files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project = Path(tmpdir)
            
            (project / "file1.py").write_text("def func1(): pass")
            (project / "file2.py").write_text("def func2(): pass")
            (project / "subdir").mkdir()
            (project / "subdir" / "file3.py").write_text("def func3(): pass")

            indexer = PythonIndexer(project)
            result = indexer.index_directory(project)

            assert len(result.files_processed) == 3
            assert len(result.symbols) == 3

    def test_syntax_error_handling(self):
        """Test handling of syntax errors."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "bad.py"
            file_path.write_text("def broken(")  # Incomplete

            indexer = PythonIndexer()
            result = indexer.index_file(file_path)

            assert len(result.errors) > 0
            assert "Syntax error" in result.errors[0]

    def test_docstring_extraction(self):
        """Test extracting docstrings."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.py"
            file_path.write_text('''
def example():
    """This is a docstring."""
    pass
''')

            indexer = PythonIndexer()
            result = indexer.index_file(file_path)

            symbol = result.symbols[0]
            assert symbol.docstring == "This is a docstring."

    def test_decorator_extraction(self):
        """Test extracting decorators."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.py"
            file_path.write_text("""
@property
@cache
def expensive(): pass
""")

            indexer = PythonIndexer()
            result = indexer.index_file(file_path)

            symbol = result.symbols[0]
            decorators = symbol.metadata.get("decorators", [])
            assert "property" in decorators or len(decorators) > 0

    def test_performance_large_file(self):
        """Test indexing performance on larger file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "large.py"
            
            # Generate file with 100 functions
            lines = []
            for i in range(100):
                lines.append(f"def func{i}(x: int) -> int:")
                lines.append(f"    return x + {i}")
                lines.append("")
            
            file_path.write_text("\n".join(lines))

            indexer = PythonIndexer()
            result = indexer.index_file(file_path)

            # Should extract all 100 functions
            assert len(result.symbols) == 100
            
            # Should be fast (<100ms for ~300 LOC)
            assert result.duration_ms < 100

    def test_exclude_pycache(self):
        """Test excluding __pycache__ directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project = Path(tmpdir)
            
            (project / "file.py").write_text("def func(): pass")
            (project / "__pycache__").mkdir()
            (project / "__pycache__" / "cached.py").write_text("def cached(): pass")

            indexer = PythonIndexer(project)
            result = indexer.index_directory(project)

            # Should only index file.py, not __pycache__
            assert len(result.files_processed) == 1
            assert "__pycache__" not in result.files_processed[0]
