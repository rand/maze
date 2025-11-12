"""Tests for Zig indexer.

Test coverage target: 80%
"""

import tempfile
from pathlib import Path

from maze.indexer.languages.zig import ZigIndexer


class TestZigIndexer:
    """Tests for ZigIndexer."""

    def test_initialization(self):
        """Test indexer initialization."""
        indexer = ZigIndexer()
        assert indexer.language == "zig"
        assert ".zig" in indexer.file_extensions

    def test_index_simple_function(self):
        """Test indexing simple Zig function."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.zig"
            file_path.write_text(
                """
pub fn add(a: i32, b: i32) i32 {
    return a + b;
}
"""
            )

            indexer = ZigIndexer()
            result = indexer.index_file(file_path)

            assert len(result.symbols) >= 1
            func = result.symbols[0]
            assert func.name == "add"
            assert func.kind == "function"
            assert func.metadata["is_pub"] is True

    def test_index_struct(self):
        """Test indexing Zig struct."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.zig"
            file_path.write_text(
                """
pub const User = struct {
    name: []const u8,
    age: u32,
};
"""
            )

            indexer = ZigIndexer()
            result = indexer.index_file(file_path)

            structs = [s for s in result.symbols if s.kind == "struct"]
            assert len(structs) >= 1
            assert structs[0].name == "User"
            assert structs[0].metadata["is_pub"] is True

    def test_index_enum(self):
        """Test indexing Zig enum."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.zig"
            file_path.write_text(
                """
const Status = enum {
    Active,
    Inactive,
};
"""
            )

            indexer = ZigIndexer()
            result = indexer.index_file(file_path)

            enums = [s for s in result.symbols if s.kind == "enum"]
            assert len(enums) >= 1
            assert enums[0].name == "Status"

    def test_index_imports(self):
        """Test indexing Zig imports."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.zig"
            file_path.write_text(
                """
const std = @import("std");
const testing = @import("testing");
"""
            )

            indexer = ZigIndexer()
            result = indexer.index_file(file_path)

            assert len(result.imports) >= 2
            assert result.imports[0].module == "std"
            assert result.imports[1].module == "testing"

    def test_detect_tests(self):
        """Test detecting Zig test blocks."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.zig"
            file_path.write_text(
                """
test "addition" {
    try testing.expectEqual(@as(i32, 2), add(1, 1));
}

test "subtraction" {
    try testing.expectEqual(@as(i32, 0), sub(1, 1));
}
"""
            )

            indexer = ZigIndexer()
            result = indexer.index_file(file_path)

            assert len(result.tests) >= 2
            assert result.tests[0].name == "addition"
            assert result.tests[1].name == "subtraction"

    def test_style_detection(self):
        """Test Zig style detection."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.zig"
            file_path.write_text("pub fn test() void {}")

            indexer = ZigIndexer()
            result = indexer.index_file(file_path)

            assert result.style.indent_size == 4
            assert result.style.semicolons is True

    def test_index_directory(self):
        """Test indexing Zig directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project = Path(tmpdir)
            src = project / "src"
            src.mkdir()

            (src / "main.zig").write_text("pub fn main() void {}")
            (src / "lib.zig").write_text("pub fn helper() void {}")

            indexer = ZigIndexer(project)
            result = indexer.index_directory(project)

            assert len(result.files_processed) == 2
            assert len(result.symbols) >= 2

    def test_exclude_cache_directories(self):
        """Test excluding zig-cache and zig-out."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project = Path(tmpdir)

            (project / "src").mkdir()
            (project / "src" / "main.zig").write_text("pub fn main() void {}")

            (project / "zig-cache").mkdir()
            (project / "zig-cache" / "cached.zig").write_text("fn cached() void {}")

            (project / "zig-out").mkdir()
            (project / "zig-out" / "output.zig").write_text("fn output() void {}")

            indexer = ZigIndexer(project)
            result = indexer.index_directory(project)

            assert len(result.files_processed) == 1
            assert "zig-cache" not in result.files_processed[0]
            assert "zig-out" not in result.files_processed[0]

    def test_performance_large_file(self):
        """Test indexing performance."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "large.zig"

            # Generate 50 functions
            lines = []
            for i in range(50):
                lines.append(f"pub fn func{i}(x: i32) i32 {{")
                lines.append(f"    return x + {i};")
                lines.append("}")

            file_path.write_text("\n".join(lines))

            indexer = ZigIndexer()
            result = indexer.index_file(file_path)

            assert len(result.symbols) >= 50
            assert result.duration_ms < 100
