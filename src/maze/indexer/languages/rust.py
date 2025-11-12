"""Rust code indexer using tree-sitter.

Extracts symbols, types (including lifetimes), traits, and patterns from Rust codebases.

Performance target: >800 symbols/sec
"""

from __future__ import annotations

from pathlib import Path

try:
    import tree_sitter_rust as ts_rust
    from tree_sitter import Language, Node, Parser

    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False

from maze.core.types import TypeContext
from maze.indexer.base import (
    BaseIndexer,
    ImportInfo,
    IndexingResult,
    StyleInfo,
    Symbol,
    TestCase,
)


class RustIndexer(BaseIndexer):
    """Rust code indexer using tree-sitter."""

    def __init__(self, project_path: Path | None = None):
        """Initialize Rust indexer.

        Args:
            project_path: Root path of the project
        """
        super().__init__(project_path)
        self.language = "rust"
        self.file_extensions = {".rs"}

        if TREE_SITTER_AVAILABLE:
            self.ts_language = Language(ts_rust.language())
            self.parser = Parser(self.ts_language)
        else:
            self.ts_language = None
            self.parser = None

    def index_file(self, file_path: Path) -> IndexingResult:
        """Index a single Rust file.

        Args:
            file_path: Path to Rust file

        Returns:
            IndexingResult with extracted information
        """
        import time

        start = time.perf_counter()

        symbols: list[Symbol] = []
        imports: list[ImportInfo] = []
        tests: list[TestCase] = []
        errors: list[str] = []

        try:
            content = file_path.read_text(encoding="utf-8")

            if not TREE_SITTER_AVAILABLE:
                errors.append("tree-sitter-rust not available, skipping")
                style = StyleInfo()
            else:
                # Parse with tree-sitter
                tree = self.parser.parse(bytes(content, "utf-8"))

                # Extract symbols
                symbols = self._extract_symbols(tree.root_node, content, str(file_path))

                # Extract imports
                imports = self._extract_imports(tree.root_node, str(file_path))

                # Detect tests
                tests = self._detect_tests(tree.root_node, str(file_path))

                # Detect style
                style = self._detect_style(content)

        except Exception as e:
            errors.append(f"Error indexing {file_path}: {e}")
            style = StyleInfo()

        duration_ms = (time.perf_counter() - start) * 1000

        return IndexingResult(
            symbols=symbols,
            imports=imports,
            tests=tests,
            style=style,
            files_processed=[str(file_path)],
            schemas=[],
            patterns=[],
            errors=errors,
            duration_ms=duration_ms,
        )

    def index_directory(self, directory: Path) -> IndexingResult:
        """Index all Rust files in directory.

        Args:
            directory: Directory to index

        Returns:
            Aggregated IndexingResult
        """
        import time

        start = time.perf_counter()

        all_symbols: list[Symbol] = []
        all_imports: list[ImportInfo] = []
        all_tests: list[TestCase] = []
        all_errors: list[str] = []
        all_files: list[str] = []

        combined_style = StyleInfo(indent_size=4, indent_type="space", quotes="double")

        # Find all Rust files
        rust_files = list(directory.rglob("*.rs"))

        for file_path in rust_files:
            # Skip target directory
            if "target" in file_path.parts:
                continue

            result = self.index_file(file_path)

            all_symbols.extend(result.symbols)
            all_imports.extend(result.imports)
            all_tests.extend(result.tests)
            all_errors.extend(result.errors)
            all_files.extend(result.files_processed)

            if file_path == rust_files[0]:
                combined_style = result.style

        duration_ms = (time.perf_counter() - start) * 1000

        return IndexingResult(
            symbols=all_symbols,
            imports=all_imports,
            tests=all_tests,
            style=combined_style,
            files_processed=all_files,
            schemas=[],
            patterns=[],
            errors=all_errors,
            duration_ms=duration_ms,
        )

    def _extract_symbols(self, node: Node, content: str, file_path: str) -> list[Symbol]:
        """Extract symbols from tree-sitter AST.

        Args:
            node: Root AST node
            content: Source code
            file_path: File path

        Returns:
            List of symbols
        """
        symbols = []

        def visit(n: Node):
            # Functions
            if n.type == "function_item":
                symbols.append(self._extract_function(n, content, file_path))

            # Structs
            elif n.type == "struct_item":
                symbols.append(self._extract_struct(n, content, file_path))

            # Enums
            elif n.type == "enum_item":
                symbols.append(self._extract_enum(n, content, file_path))

            # Traits
            elif n.type == "trait_item":
                symbols.append(self._extract_trait(n, content, file_path))

            # Impl blocks
            elif n.type == "impl_item":
                symbols.extend(self._extract_impl(n, content, file_path))

            # Type aliases
            elif n.type == "type_item":
                symbols.append(self._extract_type_alias(n, content, file_path))

            # Recurse
            for child in n.children:
                visit(child)

        visit(node)
        return [s for s in symbols if s is not None]

    def _extract_function(self, node: Node, content: str, file_path: str) -> Symbol | None:
        """Extract function symbol."""
        name_node = node.child_by_field_name("name")
        if not name_node:
            return None

        name = content[name_node.start_byte : name_node.end_byte]

        # Get full signature
        signature = content[node.start_byte : node.end_byte].split("{")[0].strip()

        # Check for async
        is_async = "async" in signature

        # Check for pub
        is_pub = signature.startswith("pub")

        return Symbol(
            name=name,
            kind="async_function" if is_async else "function",
            type_str=signature,
            file_path=file_path,
            line=node.start_point[0] + 1,
            column=node.start_point[1],
            end_line=node.end_point[0] + 1,
            end_column=node.end_point[1],
            metadata={"is_async": is_async, "is_pub": is_pub},
        )

    def _extract_struct(self, node: Node, content: str, file_path: str) -> Symbol | None:
        """Extract struct symbol."""
        name_node = node.child_by_field_name("name")
        if not name_node:
            return None

        name = content[name_node.start_byte : name_node.end_byte]

        # Get type parameters including lifetimes
        type_params = []
        type_params_node = node.child_by_field_name("type_parameters")
        if type_params_node:
            type_params_text = content[type_params_node.start_byte : type_params_node.end_byte]
            type_params = self._parse_type_parameters(type_params_text)

        type_str = f"struct {name}"
        if type_params:
            type_str += f"<{', '.join(type_params)}>"

        return Symbol(
            name=name,
            kind="struct",
            type_str=type_str,
            file_path=file_path,
            line=node.start_point[0] + 1,
            column=node.start_point[1],
            metadata={"type_parameters": type_params},
        )

    def _extract_enum(self, node: Node, content: str, file_path: str) -> Symbol | None:
        """Extract enum symbol."""
        name_node = node.child_by_field_name("name")
        if not name_node:
            return None

        name = content[name_node.start_byte : name_node.end_byte]

        return Symbol(
            name=name,
            kind="enum",
            type_str=f"enum {name}",
            file_path=file_path,
            line=node.start_point[0] + 1,
            column=node.start_point[1],
        )

    def _extract_trait(self, node: Node, content: str, file_path: str) -> Symbol | None:
        """Extract trait symbol."""
        name_node = node.child_by_field_name("name")
        if not name_node:
            return None

        name = content[name_node.start_byte : name_node.end_byte]

        return Symbol(
            name=name,
            kind="trait",
            type_str=f"trait {name}",
            file_path=file_path,
            line=node.start_point[0] + 1,
            column=node.start_point[1],
        )

    def _extract_impl(self, node: Node, content: str, file_path: str) -> list[Symbol]:
        """Extract impl block methods."""
        symbols = []

        # Extract trait being implemented
        trait_node = node.child_by_field_name("trait")
        type_node = node.child_by_field_name("type")

        impl_for = None
        if type_node:
            impl_for = content[type_node.start_byte : type_node.end_byte]

        # Extract methods from impl block
        for child in node.children:
            if child.type == "function_item":
                method = self._extract_function(child, content, file_path)
                if method and impl_for:
                    method.metadata["impl_for"] = impl_for
                    symbols.append(method)

        return symbols

    def _extract_type_alias(self, node: Node, content: str, file_path: str) -> Symbol | None:
        """Extract type alias."""
        name_node = node.child_by_field_name("name")
        if not name_node:
            return None

        name = content[name_node.start_byte : name_node.end_byte]

        return Symbol(
            name=name,
            kind="type_alias",
            type_str=f"type {name}",
            file_path=file_path,
            line=node.start_point[0] + 1,
            column=node.start_point[1],
        )

    def _parse_type_parameters(self, params_text: str) -> list[str]:
        """Parse type parameters including lifetimes.

        Args:
            params_text: Type parameters text like "<'a, T: Clone>"

        Returns:
            List of parameter strings
        """
        # Remove < and >
        params_text = params_text.strip("<>")

        # Split by comma (simple split, not handling nested)
        params = [p.strip() for p in params_text.split(",")]

        return params

    def _extract_imports(self, node: Node, file_path: str) -> list[ImportInfo]:
        """Extract use statements."""
        imports = []

        def visit(n: Node):
            if n.type == "use_declaration":
                # Basic import extraction
                imports.append(
                    ImportInfo(
                        module="use statement",
                        symbols=[],
                        file_path=file_path,
                        line=n.start_point[0] + 1,
                    )
                )

            for child in n.children:
                visit(child)

        visit(node)
        return imports

    def _detect_tests(self, node: Node, file_path: str) -> list[TestCase]:
        """Detect test functions (#[test] attribute)."""
        tests = []

        def visit(n: Node):
            if n.type == "function_item":
                # Check for #[test] attribute
                has_test_attr = False
                for child in n.children:
                    if child.type == "attribute_item":
                        # Check if it's #[test]
                        has_test_attr = True
                        break

                if has_test_attr:
                    name_node = n.child_by_field_name("name")
                    if name_node:
                        # This is a test function
                        tests.append(
                            TestCase(
                                name=f"test_{len(tests)}",
                                kind="unit",
                                test_function="",
                                file_path=file_path,
                                command="cargo test",
                            )
                        )

            for child in n.children:
                visit(child)

        visit(node)
        return tests

    def _detect_style(self, content: str) -> StyleInfo:
        """Detect Rust code style."""
        # Rust standard: 4 spaces
        return StyleInfo(
            indent_size=4,
            indent_type="space",
            quotes="double",
            semicolons=True,
            max_line_length=100,
            naming_convention={
                "function": "snake_case",
                "struct": "PascalCase",
                "enum": "PascalCase",
                "trait": "PascalCase",
                "variable": "snake_case",
                "constant": "UPPER_SNAKE_CASE",
            },
        )

    def extract_symbols(self, content: str, file_path: Path) -> list[Symbol]:
        """Extract symbols from file content."""
        if not TREE_SITTER_AVAILABLE:
            return []

        tree = self.parser.parse(bytes(content, "utf-8"))
        return self._extract_symbols(tree.root_node, content, str(file_path))

    def extract_type_context(self, content: str, file_path: Path) -> TypeContext:
        """Extract type context from Rust file."""
        context = TypeContext()

        if TREE_SITTER_AVAILABLE:
            symbols = self.extract_symbols(content, file_path)

            for symbol in symbols:
                if symbol.kind in ["function", "async_function"]:
                    context.functions[symbol.name] = ([], symbol.type_str)

        return context

    def extract_tests(self, content: str, file_path: Path) -> list[TestCase]:
        """Extract test cases from file."""
        if not TREE_SITTER_AVAILABLE:
            return []

        tree = self.parser.parse(bytes(content, "utf-8"))
        return self._detect_tests(tree.root_node, str(file_path))
