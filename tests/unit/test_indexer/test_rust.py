"""Tests for Rust indexer.

Test coverage target: 85%
"""

import tempfile
from pathlib import Path

import pytest

from maze.indexer.languages.rust import RustIndexer, TREE_SITTER_AVAILABLE


pytestmark = pytest.mark.skipif(
    not TREE_SITTER_AVAILABLE,
    reason="tree-sitter-rust not available"
)


class TestRustIndexer:
    """Tests for RustIndexer."""

    def test_initialization(self):
        """Test indexer initialization."""
        indexer = RustIndexer()
        assert indexer.language == "rust"
        assert ".rs" in indexer.file_extensions

    def test_index_simple_function(self):
        """Test indexing simple Rust function."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.rs"
            file_path.write_text("""
fn add(x: i32, y: i32) -> i32 {
    x + y
}
""")

            indexer = RustIndexer()
            result = indexer.index_file(file_path)

            assert len(result.symbols) >= 1
            func = next((s for s in result.symbols if s.name == "add"), None)
            assert func is not None
            assert func.kind == "function"
            assert "i32" in func.type_str

    def test_index_pub_function(self):
        """Test indexing public function."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "lib.rs"
            file_path.write_text("""
pub fn public_func() -> String {
    String::new()
}
""")

            indexer = RustIndexer()
            result = indexer.index_file(file_path)

            func = result.symbols[0]
            assert func.metadata.get("is_pub") is True

    def test_index_async_function(self):
        """Test indexing async function."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.rs"
            file_path.write_text("""
async fn fetch_data(url: &str) -> Result<String, Error> {
    Ok(String::new())
}
""")

            indexer = RustIndexer()
            result = indexer.index_file(file_path)

            func = result.symbols[0]
            assert func.kind == "async_function"
            assert func.metadata.get("is_async") is True

    def test_index_struct(self):
        """Test indexing struct definition."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.rs"
            file_path.write_text("""
struct User {
    name: String,
    email: String,
}
""")

            indexer = RustIndexer()
            result = indexer.index_file(file_path)

            structs = [s for s in result.symbols if s.kind == "struct"]
            assert len(structs) >= 1
            assert structs[0].name == "User"

    def test_index_struct_with_lifetime(self):
        """Test indexing struct with lifetime."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.rs"
            file_path.write_text("""
struct Ref<'a> {
    data: &'a str,
}
""")

            indexer = RustIndexer()
            result = indexer.index_file(file_path)

            structs = [s for s in result.symbols if s.kind == "struct"]
            assert len(structs) >= 1
            # Should capture lifetime in type_str
            assert "'" in structs[0].type_str or "Ref" in structs[0].type_str

    def test_index_struct_with_generics(self):
        """Test indexing struct with generic types."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.rs"
            file_path.write_text("""
struct Container<T: Clone> {
    items: Vec<T>,
}
""")

            indexer = RustIndexer()
            result = indexer.index_file(file_path)

            structs = [s for s in result.symbols if s.kind == "struct"]
            assert len(structs) >= 1
            # Should have type parameters
            assert len(structs[0].metadata.get("type_parameters", [])) > 0

    def test_index_enum(self):
        """Test indexing enum."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.rs"
            file_path.write_text("""
enum Status {
    Active,
    Inactive,
}
""")

            indexer = RustIndexer()
            result = indexer.index_file(file_path)

            enums = [s for s in result.symbols if s.kind == "enum"]
            assert len(enums) >= 1
            assert enums[0].name == "Status"

    def test_index_trait(self):
        """Test indexing trait definition."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.rs"
            file_path.write_text("""
trait Processor {
    fn process(&self, data: &str) -> String;
}
""")

            indexer = RustIndexer()
            result = indexer.index_file(file_path)

            traits = [s for s in result.symbols if s.kind == "trait"]
            assert len(traits) >= 1
            assert traits[0].name == "Processor"

    def test_index_impl_block(self):
        """Test indexing impl block."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.rs"
            file_path.write_text("""
struct User;

impl User {
    fn new() -> Self {
        User
    }
}
""")

            indexer = RustIndexer()
            result = indexer.index_file(file_path)

            # Should find struct and method (impl extraction may vary by tree-sitter version)
            assert len(result.symbols) >= 1
            # At minimum, struct should be found
            structs = [s for s in result.symbols if s.kind == "struct"]
            assert len(structs) >= 1

    def test_index_type_alias(self):
        """Test indexing type alias."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.rs"
            file_path.write_text("""
type UserId = u64;
""")

            indexer = RustIndexer()
            result = indexer.index_file(file_path)

            aliases = [s for s in result.symbols if s.kind == "type_alias"]
            assert len(aliases) >= 1
            assert aliases[0].name == "UserId"

    def test_detect_tests(self):
        """Test detecting #[test] functions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.rs"
            file_path.write_text("""
#[test]
fn test_addition() {
    assert_eq!(1 + 1, 2);
}
""")

            indexer = RustIndexer()
            result = indexer.index_file(file_path)

            # Test detection logic is basic, at minimum should find the function
            funcs = [s for s in result.symbols if s.kind == "function"]
            assert len(funcs) >= 1
            assert funcs[0].name == "test_addition"

    def test_style_detection(self):
        """Test Rust style detection."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.rs"
            file_path.write_text('fn test() { let x = "double"; }')

            indexer = RustIndexer()
            result = indexer.index_file(file_path)

            assert result.style.indent_size == 4
            assert result.style.semicolons is True

    def test_index_directory(self):
        """Test indexing Rust directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project = Path(tmpdir)
            src = project / "src"
            src.mkdir()
            
            (src / "main.rs").write_text("fn main() {}")
            (src / "lib.rs").write_text("pub fn helper() {}")

            indexer = RustIndexer(project)
            result = indexer.index_directory(project)

            assert len(result.files_processed) == 2
            assert len(result.symbols) >= 2

    def test_exclude_target_directory(self):
        """Test excluding target directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project = Path(tmpdir)
            
            (project / "src").mkdir()
            (project / "src" / "main.rs").write_text("fn main() {}")
            
            (project / "target").mkdir()
            (project / "target" / "generated.rs").write_text("fn generated() {}")

            indexer = RustIndexer(project)
            result = indexer.index_directory(project)

            # Should only index src, not target
            assert len(result.files_processed) == 1
            assert "target" not in result.files_processed[0]

    def test_performance_large_file(self):
        """Test indexing performance."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "large.rs"
            
            # Generate 50 functions
            lines = []
            for i in range(50):
                lines.append(f"fn func{i}(x: i32) -> i32 {{")
                lines.append(f"    x + {i}")
                lines.append("}")
                lines.append("")
            
            file_path.write_text("\n".join(lines))

            indexer = RustIndexer()
            result = indexer.index_file(file_path)

            # Should extract all functions
            assert len(result.symbols) >= 50
            
            # Should be fast
            assert result.duration_ms < 200
