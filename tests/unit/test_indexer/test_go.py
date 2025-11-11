"""Tests for Go indexer.

Test coverage target: 85%
"""

import tempfile
from pathlib import Path

import pytest

from maze.indexer.languages.go import GoIndexer, TREE_SITTER_AVAILABLE


pytestmark = pytest.mark.skipif(
    not TREE_SITTER_AVAILABLE,
    reason="tree-sitter-go not available"
)


class TestGoIndexer:
    """Tests for GoIndexer."""

    def test_initialization(self):
        """Test indexer initialization."""
        indexer = GoIndexer()
        assert indexer.language == "go"
        assert ".go" in indexer.file_extensions

    def test_index_simple_function(self):
        """Test indexing simple Go function."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.go"
            file_path.write_text("""
package main

func Add(x, y int) int {
    return x + y
}
""")

            indexer = GoIndexer()
            result = indexer.index_file(file_path)

            funcs = [s for s in result.symbols if s.kind == "function"]
            assert len(funcs) >= 1
            assert funcs[0].name == "Add"

    def test_index_method(self):
        """Test indexing method on struct."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.go"
            file_path.write_text("""
package main

type Service struct{}

func (s *Service) Start() error {
    return nil
}
""")

            indexer = GoIndexer()
            result = indexer.index_file(file_path)

            methods = [s for s in result.symbols if s.kind == "method"]
            assert len(methods) >= 1
            assert methods[0].name == "Start"

    def test_index_struct(self):
        """Test indexing struct."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.go"
            file_path.write_text("""
package main

type User struct {
    ID   string
    Name string
}
""")

            indexer = GoIndexer()
            result = indexer.index_file(file_path)

            structs = [s for s in result.symbols if s.kind == "struct"]
            assert len(structs) >= 1
            assert structs[0].name == "User"

    def test_index_interface(self):
        """Test indexing interface."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.go"
            file_path.write_text("""
package main

type Repository interface {
    Find(id string) (*User, error)
    Save(user *User) error
}
""")

            indexer = GoIndexer()
            result = indexer.index_file(file_path)

            interfaces = [s for s in result.symbols if s.kind == "interface"]
            assert len(interfaces) >= 1
            assert interfaces[0].name == "Repository"

    def test_index_type_alias(self):
        """Test indexing type alias."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.go"
            file_path.write_text("""
package main

type UserID string
""")

            indexer = GoIndexer()
            result = indexer.index_file(file_path)

            types = [s for s in result.symbols if s.kind == "type_alias"]
            assert len(types) >= 1
            assert types[0].name == "UserID"

    def test_detect_test_functions(self):
        """Test detecting Go test functions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test_test.go"
            file_path.write_text("""
package main

import "testing"

func TestAddition(t *testing.T) {
    if Add(1, 1) != 2 {
        t.Error("Expected 2")
    }
}
""")

            indexer = GoIndexer()
            result = indexer.index_file(file_path)

            assert len(result.tests) >= 1
            assert result.tests[0].name == "TestAddition"

    def test_style_detection(self):
        """Test Go style detection."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.go"
            file_path.write_text('package main\n\nfunc Test() {}')

            indexer = GoIndexer()
            result = indexer.index_file(file_path)

            assert result.style.indent_type == "tab"

    def test_index_directory(self):
        """Test indexing Go directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project = Path(tmpdir)
            
            (project / "main.go").write_text("package main\n\nfunc main() {}")
            (project / "helper.go").write_text("package main\n\nfunc Helper() {}")

            indexer = GoIndexer(project)
            result = indexer.index_directory(project)

            assert len(result.files_processed) == 2
            assert len(result.symbols) >= 2

    def test_exclude_vendor(self):
        """Test excluding vendor directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project = Path(tmpdir)
            
            (project / "main.go").write_text("package main\n\nfunc main() {}")
            (project / "vendor").mkdir()
            (project / "vendor" / "lib.go").write_text("package lib\n\nfunc Lib() {}")

            indexer = GoIndexer(project)
            result = indexer.index_directory(project)

            assert len(result.files_processed) == 1
            assert "vendor" not in result.files_processed[0]
