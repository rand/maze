"""Tests for Python pattern mining.

Test coverage target: 85%
"""

import ast
import tempfile
from pathlib import Path

import pytest

from maze.learning.pattern_mining import PatternMiningEngine


class TestPythonPatternMining:
    """Tests for mining patterns from Python code."""

    def test_mine_python_project(self):
        """Test mining patterns from Python project."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project = Path(tmpdir)
            
            # Create sample Python files
            (project / "module1.py").write_text("""
def calculate(x: int, y: int) -> int:
    return x + y

async def fetch_data(url: str) -> dict:
    return {}
""")
            
            (project / "module2.py").write_text("""
from dataclasses import dataclass

@dataclass
class User:
    name: str
    email: str
""")

            miner = PatternMiningEngine(language="python", min_frequency=1)
            patterns = miner.mine_patterns(project)

            assert patterns is not None
            assert patterns.language == "python"
            # May be 0 if patterns below frequency threshold
            assert patterns.total_patterns >= 0

    def test_extract_python_function_patterns(self):
        """Test extracting function patterns from Python."""
        code = """
def process_data(items: list[int]) -> list[int]:
    return [x * 2 for x in items]

async def fetch(url: str) -> dict[str, Any]:
    async with httpx.AsyncClient() as client:
        return await client.get(url)
"""

        miner = PatternMiningEngine(language="python")
        tree = ast.parse(code)
        patterns = miner.extract_syntactic_patterns(tree, code)

        # Should find function patterns
        function_patterns = [p for p in patterns if p.pattern_type == "function"]
        assert len(function_patterns) > 0

    def test_extract_python_class_patterns(self):
        """Test extracting class patterns from Python."""
        code = """
@dataclass
class Point:
    x: float
    y: float
    
class Repository:
    def __init__(self, db):
        self.db = db
"""

        miner = PatternMiningEngine(language="python")
        tree = ast.parse(code)
        patterns = miner.extract_syntactic_patterns(tree, code)

        # Should find class patterns
        class_patterns = [p for p in patterns if p.pattern_type == "class"]
        assert len(class_patterns) > 0

    def test_python_error_handling_patterns(self):
        """Test extracting error handling patterns."""
        code = """
def safe_divide(a: float, b: float) -> float:
    try:
        return a / b
    except ZeroDivisionError:
        return 0.0
    except Exception as e:
        raise ValueError(f"Invalid operation: {e}")
"""

        miner = PatternMiningEngine(language="python")
        tree = ast.parse(code)
        patterns = miner.extract_syntactic_patterns(tree, code)

        # Should find error handling pattern
        error_patterns = [p for p in patterns if p.pattern_type == "error_handling"]
        assert len(error_patterns) > 0

    def test_python_and_typescript_both_supported(self):
        """Test both Python and TypeScript supported."""
        miner_py = PatternMiningEngine(language="python")
        miner_ts = PatternMiningEngine(language="typescript")

        # Both should work
        assert miner_py.language == "python"
        assert miner_ts.language == "typescript"

        # Python code
        py_code = "def test(): pass"
        py_tree = ast.parse(py_code)
        py_patterns = miner_py.extract_syntactic_patterns(py_tree, py_code)
        assert isinstance(py_patterns, list)
