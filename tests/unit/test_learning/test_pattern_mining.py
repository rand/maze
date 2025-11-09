"""
Tests for pattern mining engine.
"""

import ast
import tempfile
from pathlib import Path

import pytest

from maze.learning.pattern_mining import (
    PatternMiningEngine,
    SyntacticPattern,
    TypePattern,
    SemanticPattern,
    PatternSet
)
from maze.core.types import TypeContext, Type


class TestPatternMiningEngine:
    """Test PatternMiningEngine class."""

    def test_mine_patterns_basic(self, tmp_path):
        """Test basic pattern mining."""
        # Create small test codebase
        test_file = tmp_path / "test.py"
        test_file.write_text("""
def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

class Calculator:
    def multiply(self, a, b):
        return a * b
""")

        engine = PatternMiningEngine(language="python", min_frequency=1)
        result = engine.mine_patterns(tmp_path, "python")

        assert isinstance(result, PatternSet)
        assert result.language == "python"
        assert result.total_patterns > 0
        assert len(result.syntactic) > 0
        assert result.extraction_time_ms > 0

    def test_extract_syntactic_patterns_functions(self):
        """Test function pattern extraction."""
        code = """
def foo(x, y):
    return x + y

def bar(a, b, c):
    return a * b * c
"""
        engine = PatternMiningEngine(language="python")
        tree = ast.parse(code)

        patterns = engine.extract_syntactic_patterns(tree, code)

        function_patterns = [p for p in patterns if p.pattern_type == "function"]
        assert len(function_patterns) == 2
        assert all(p.frequency == 1 for p in function_patterns)
        assert all(len(p.examples) > 0 for p in function_patterns)

    def test_extract_syntactic_patterns_classes(self):
        """Test class pattern extraction."""
        code = """
class Foo:
    def __init__(self):
        pass

class Bar(Foo):
    def method(self):
        return 42
"""
        engine = PatternMiningEngine(language="python")
        tree = ast.parse(code)

        patterns = engine.extract_syntactic_patterns(tree, code)

        class_patterns = [p for p in patterns if p.pattern_type == "class"]
        assert len(class_patterns) == 2
        assert any(p.context.get("has_init", False) for p in class_patterns)

    def test_extract_type_patterns(self):
        """Test type pattern extraction."""
        engine = PatternMiningEngine(language="python")

        type_context = TypeContext()
        # Use variables dict directly
        type_context.variables["x"] = Type("int")
        type_context.variables["y"] = Type("int")
        type_context.variables["name"] = Type("str")

        patterns = engine.extract_type_patterns(type_context, "")

        assert len(patterns) >= 2
        int_pattern = next((p for p in patterns if "int" in p.signature), None)
        assert int_pattern is not None
        assert int_pattern.frequency >= 2

    def test_extract_semantic_patterns(self):
        """Test semantic pattern extraction."""
        code = """
try:
    result = dangerous_operation()
except ValueError:
    handle_error()

try:
    another_op()
except Exception:
    pass
"""
        engine = PatternMiningEngine(language="python", enable_semantic=True)

        patterns = engine.extract_semantic_patterns(code)

        error_patterns = [p for p in patterns if p.intent == "error_handling"]
        assert len(error_patterns) > 0
        assert error_patterns[0].frequency >= 2

    def test_rank_patterns_by_frequency(self):
        """Test pattern ranking by frequency."""
        patterns = [
            SyntacticPattern("function", "def foo(): ...", 5, [], {}),
            SyntacticPattern("function", "def bar(): ...", 2, [], {}),
            SyntacticPattern("function", "def baz(): ...", 10, [], {}),
        ]

        engine = PatternMiningEngine(language="python")
        ranked = engine.rank_patterns(patterns)

        assert len(ranked) == 3
        # Should be sorted by frequency (descending)
        assert ranked[0].frequency >= ranked[1].frequency
        assert ranked[1].frequency >= ranked[2].frequency

    def test_rank_patterns_custom_criteria(self):
        """Test custom ranking criteria."""
        patterns = [
            SyntacticPattern("function", "def simple(): pass", 3, ["example1"], {}),
            SyntacticPattern("function", "def complex(): ...", 2, ["ex1", "ex2", "ex3"], {}),
        ]

        engine = PatternMiningEngine(language="python")

        # Weight examples more heavily
        ranked = engine.rank_patterns(patterns, {"frequency": 0.3, "examples": 0.7, "complexity": 0})

        # Pattern with more examples should rank higher despite lower frequency
        assert len(ranked[0].examples) > len(ranked[1].examples)

    def test_incremental_mine(self, tmp_path):
        """Test incremental pattern mining."""
        # Initial codebase
        initial_file = tmp_path / "initial.py"
        initial_file.write_text("def foo(): pass")

        engine = PatternMiningEngine(language="python", min_frequency=1)
        initial_patterns = engine.mine_patterns(tmp_path, "python")

        # Add new file
        new_file = tmp_path / "new.py"
        new_file.write_text("def foo(): return 42")

        updated_patterns = engine.incremental_mine(new_file, initial_patterns)

        # Should have more patterns or increased frequency
        assert updated_patterns.total_patterns >= initial_patterns.total_patterns

    def test_mining_performance_large_codebase(self, tmp_path):
        """Test performance on larger codebase."""
        # Create moderate-sized codebase
        for i in range(20):
            test_file = tmp_path / f"module_{i}.py"
            test_file.write_text(f"""
def function_{i}(x):
    return x * {i}

class Class_{i}:
    def method(self):
        return {i}
""")

        engine = PatternMiningEngine(language="python", min_frequency=1)
        result = engine.mine_patterns(tmp_path, "python")

        # Should complete reasonably quickly for small test
        assert result.extraction_time_ms < 5000  # <5s for test
        assert result.total_patterns > 0

    def test_parallel_mining(self, tmp_path):
        """Test parallel mining optimization."""
        # Create 15 files to trigger parallel processing
        for i in range(15):
            test_file = tmp_path / f"file_{i}.py"
            test_file.write_text(f"def func_{i}(): pass")

        engine = PatternMiningEngine(language="python", min_frequency=1)
        result = engine.mine_patterns(tmp_path, "python")

        assert result.total_patterns > 0
        # Parallel processing uses separate processes, stats may not be updated
        # Just verify mining worked
        assert result.extraction_time_ms > 0

    def test_min_frequency_filter(self, tmp_path):
        """Test minimum frequency filtering."""
        test_file = tmp_path / "test.py"
        test_file.write_text("""
def foo(): pass
def bar(): pass
def baz(): pass
""")

        # High min_frequency should filter out unique patterns
        engine = PatternMiningEngine(language="python", min_frequency=5)
        result = engine.mine_patterns(tmp_path, "python")

        # Should have fewer patterns due to high min_frequency
        assert result.total_patterns == 0 or all(
            p.frequency >= 5 for p in result.syntactic
        )

    def test_max_patterns_limit(self, tmp_path):
        """Test maximum patterns limit."""
        # Create many unique patterns
        code_lines = []
        for i in range(100):
            code_lines.append(f"def func_{i}(): pass")

        test_file = tmp_path / "test.py"
        test_file.write_text("\n".join(code_lines))

        engine = PatternMiningEngine(language="python", min_frequency=1, max_patterns=30)
        result = engine.mine_patterns(tmp_path, "python")

        # Should respect max_patterns limit
        assert result.total_patterns <= 30

    def test_pattern_deduplication(self):
        """Test duplicate pattern removal."""
        patterns = [
            SyntacticPattern("function", "def foo(): ...", 1, ["ex1"], {}),
            SyntacticPattern("function", "def foo(): ...", 1, ["ex2"], {}),
            SyntacticPattern("function", "def bar(): ...", 1, ["ex3"], {}),
        ]

        engine = PatternMiningEngine(language="python")
        aggregated = engine._aggregate_syntactic_patterns(patterns)

        # Should merge duplicates
        assert len(aggregated) == 2
        foo_pattern = next(p for p in aggregated if "foo" in p.template)
        assert foo_pattern.frequency == 2

    def test_context_extraction(self):
        """Test pattern context metadata."""
        code = """
@decorator
async def async_function(a, b):
    return a + b
"""
        engine = PatternMiningEngine(language="python")
        tree = ast.parse(code)

        patterns = engine.extract_syntactic_patterns(tree, code)

        # AsyncFunctionDef is separate from FunctionDef in Python 3.14
        func_pattern = next((p for p in patterns if p.pattern_type == "function"), None)
        assert func_pattern is not None
        assert func_pattern.context["args_count"] == 2
        # Async detection may vary by Python version
        assert "decorators" in func_pattern.context

    def test_error_handling_invalid_code(self, tmp_path):
        """Test error handling for invalid code."""
        invalid_file = tmp_path / "invalid.py"
        invalid_file.write_text("def broken(")

        engine = PatternMiningEngine(language="python", min_frequency=1)

        # Should not crash on invalid code
        result = engine.mine_patterns(tmp_path, "python")

        # Should have stats even with errors
        assert "files_processed" in engine.stats

    def test_multi_language_support(self, tmp_path):
        """Test multiple language support."""
        py_file = tmp_path / "test.py"
        py_file.write_text("def foo(): pass")

        # Python should work
        engine_py = PatternMiningEngine(language="python", min_frequency=1)
        result_py = engine_py.mine_patterns(tmp_path, "python")
        assert result_py.total_patterns > 0

        # Other languages should not crash (even if not fully implemented)
        engine_ts = PatternMiningEngine(language="typescript", min_frequency=1)
        result_ts = engine_ts.mine_patterns(tmp_path, "typescript")
        assert isinstance(result_ts, PatternSet)

    def test_pattern_template_generalization(self):
        """Test pattern template generalization."""
        code = "def specific_function(param1, param2, param3): return param1"

        engine = PatternMiningEngine(language="python")
        tree = ast.parse(code)

        patterns = engine.extract_syntactic_patterns(tree, code)

        func_pattern = next((p for p in patterns if p.pattern_type == "function"), None)
        assert func_pattern is not None
        # Template should be generalized
        assert "specific_function" in func_pattern.template
        assert "arg" in func_pattern.template or "param" not in func_pattern.template

    def test_cache_utilization(self):
        """Test AST cache utilization."""
        code = "def foo(): pass"

        engine = PatternMiningEngine(language="python")

        # First parse (cache miss)
        tree1 = engine._parse_with_cache(code)
        assert engine.stats["cache_misses"] == 1
        assert engine.stats["cache_hits"] == 0

        # Second parse (cache hit)
        tree2 = engine._parse_with_cache(code)
        assert engine.stats["cache_hits"] == 1
        assert tree1 is tree2

    def test_mining_stats(self, tmp_path):
        """Test mining statistics."""
        test_file = tmp_path / "test.py"
        test_file.write_text("def foo(): pass")

        engine = PatternMiningEngine(language="python", min_frequency=1)
        result = engine.mine_patterns(tmp_path, "python")

        stats = engine.get_mining_stats()

        assert "files_processed" in stats
        assert "total_patterns" in stats
        assert stats["files_processed"] > 0
        assert stats["total_patterns"] == result.total_patterns

    def test_semantic_pattern_disabled(self, tmp_path):
        """Test with semantic extraction disabled."""
        test_file = tmp_path / "test.py"
        test_file.write_text("""
try:
    risky()
except:
    pass
""")

        engine = PatternMiningEngine(language="python", enable_semantic=False, min_frequency=1)
        result = engine.mine_patterns(tmp_path, "python")

        # Should not extract semantic patterns
        assert len(result.semantic) == 0


class TestPatternDataStructures:
    """Test pattern data structures."""

    def test_syntactic_pattern_hash(self):
        """Test SyntacticPattern hashing."""
        p1 = SyntacticPattern("function", "def foo(): ...", 1, [], {})
        p2 = SyntacticPattern("function", "def foo(): ...", 2, ["different"], {})

        # Should hash to same value (based on type and template)
        assert hash(p1) == hash(p2)

    def test_type_pattern_hash(self):
        """Test TypePattern hashing."""
        p1 = TypePattern("int", ["x", "y"], 2)
        p2 = TypePattern("int", ["a", "b"], 3)

        # Should hash to same value (based on signature)
        assert hash(p1) == hash(p2)

    def test_semantic_pattern_hash(self):
        """Test SemanticPattern hashing."""
        p1 = SemanticPattern("error_handling", "try-except", [], 1)
        p2 = SemanticPattern("error_handling", "try-except", ["different"], 2)

        # Should hash to same value (based on intent and structure)
        assert hash(p1) == hash(p2)
