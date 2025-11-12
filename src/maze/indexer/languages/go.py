"""Go code indexer using tree-sitter.

Extracts symbols, types, interfaces, and patterns from Go codebases.

Performance target: >1000 symbols/sec
"""

from __future__ import annotations

from pathlib import Path

try:
    import tree_sitter_go as ts_go
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


class GoIndexer(BaseIndexer):
    """Go code indexer using tree-sitter."""

    def __init__(self, project_path: Path | None = None):
        """Initialize Go indexer.

        Args:
            project_path: Root path of the project
        """
        super().__init__(project_path)
        self.language = "go"
        self.file_extensions = {".go"}

        if TREE_SITTER_AVAILABLE:
            self.ts_language = Language(ts_go.language())
            self.parser = Parser(self.ts_language)
        else:
            self.ts_language = None
            self.parser = None

    def index_file(self, file_path: Path) -> IndexingResult:
        """Index a single Go file."""
        import time

        start = time.perf_counter()

        symbols: list[Symbol] = []
        imports: list[ImportInfo] = []
        tests: list[TestCase] = []
        errors: list[str] = []

        try:
            content = file_path.read_text(encoding="utf-8")

            if not TREE_SITTER_AVAILABLE:
                errors.append("tree-sitter-go not available")
                style = StyleInfo()
            else:
                tree = self.parser.parse(bytes(content, "utf-8"))
                symbols = self._extract_symbols(tree.root_node, content, str(file_path))
                imports = self._extract_imports(tree.root_node, content, str(file_path))
                tests = self._detect_tests(tree.root_node, content, str(file_path))
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
        """Index all Go files in directory."""
        import time

        start = time.perf_counter()

        all_symbols: list[Symbol] = []
        all_imports: list[ImportInfo] = []
        all_tests: list[TestCase] = []
        all_errors: list[str] = []
        all_files: list[str] = []

        combined_style = StyleInfo(indent_size=1, indent_type="tab")

        go_files = list(directory.rglob("*.go"))

        for file_path in go_files:
            if "vendor" in file_path.parts or ".git" in file_path.parts:
                continue

            result = self.index_file(file_path)
            all_symbols.extend(result.symbols)
            all_imports.extend(result.imports)
            all_tests.extend(result.tests)
            all_errors.extend(result.errors)
            all_files.extend(result.files_processed)

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
        """Extract symbols from Go AST."""
        symbols = []

        def visit(n: Node):
            if n.type == "function_declaration":
                symbols.append(self._extract_function(n, content, file_path))
            elif n.type == "method_declaration":
                symbols.append(self._extract_method(n, content, file_path))
            elif n.type == "type_declaration":
                symbols.extend(self._extract_type_decl(n, content, file_path))
            elif n.type == "interface_type":
                # Handle inline interfaces
                pass

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

        # Get signature
        sig_end = content.find("{", node.start_byte)
        if sig_end == -1:
            sig_end = node.end_byte
        signature = content[node.start_byte : sig_end].strip()

        return Symbol(
            name=name,
            kind="function",
            type_str=signature,
            file_path=file_path,
            line=node.start_point[0] + 1,
            column=node.start_point[1],
        )

    def _extract_method(self, node: Node, content: str, file_path: str) -> Symbol | None:
        """Extract method symbol."""
        name_node = node.child_by_field_name("name")
        receiver_node = node.child_by_field_name("receiver")

        if not name_node:
            return None

        name = content[name_node.start_byte : name_node.end_byte]

        receiver_type = ""
        if receiver_node:
            receiver_type = content[receiver_node.start_byte : receiver_node.end_byte]

        sig_end = content.find("{", node.start_byte)
        if sig_end == -1:
            sig_end = node.end_byte
        signature = content[node.start_byte : sig_end].strip()

        return Symbol(
            name=name,
            kind="method",
            type_str=signature,
            file_path=file_path,
            line=node.start_point[0] + 1,
            column=node.start_point[1],
            metadata={"receiver": receiver_type},
        )

    def _extract_type_decl(self, node: Node, content: str, file_path: str) -> list[Symbol]:
        """Extract type declarations (struct, interface, alias)."""
        symbols = []

        for spec in node.children:
            if spec.type == "type_spec":
                name_node = spec.child_by_field_name("name")
                type_node = spec.child_by_field_name("type")

                if name_node:
                    name = content[name_node.start_byte : name_node.end_byte]

                    if type_node:
                        type_kind = type_node.type

                        if type_kind == "struct_type":
                            kind = "struct"
                        elif type_kind == "interface_type":
                            kind = "interface"
                        else:
                            kind = "type_alias"

                        symbols.append(
                            Symbol(
                                name=name,
                                kind=kind,
                                type_str=f"{kind} {name}",
                                file_path=file_path,
                                line=spec.start_point[0] + 1,
                                column=spec.start_point[1],
                            )
                        )

        return symbols

    def _extract_imports(self, node: Node, content: str, file_path: str) -> list[ImportInfo]:
        """Extract import declarations."""
        imports = []

        def visit(n: Node):
            if n.type == "import_declaration":
                imports.append(
                    ImportInfo(
                        module="import",
                        symbols=[],
                        file_path=file_path,
                        line=n.start_point[0] + 1,
                    )
                )

            for child in n.children:
                visit(child)

        visit(node)
        return imports

    def _detect_tests(self, node: Node, content: str, file_path: str) -> list[TestCase]:
        """Detect test functions (Test* functions)."""
        tests = []

        def visit(n: Node):
            if n.type == "function_declaration":
                name_node = n.child_by_field_name("name")
                if name_node:
                    name = content[name_node.start_byte : name_node.end_byte]
                    if name.startswith("Test"):
                        tests.append(
                            TestCase(
                                name=name,
                                kind="unit",
                                test_function=name,
                                file_path=file_path,
                                command=f"go test -run {name}",
                            )
                        )

            for child in n.children:
                visit(child)

        visit(node)
        return tests

    def _detect_style(self, content: str) -> StyleInfo:
        """Detect Go code style."""
        # Go standard: tabs for indentation
        return StyleInfo(
            indent_size=1,
            indent_type="tab",
            quotes="double",
            semicolons=False,  # Go doesn't require semicolons
            max_line_length=100,
            naming_convention={
                "function": "PascalCase",  # Exported
                "struct": "PascalCase",
                "interface": "PascalCase",
                "variable": "camelCase",
                "constant": "PascalCase",
            },
        )

    def extract_symbols(self, content: str, file_path: Path) -> list[Symbol]:
        """Extract symbols from file content."""
        if not TREE_SITTER_AVAILABLE:
            return []

        tree = self.parser.parse(bytes(content, "utf-8"))
        return self._extract_symbols(tree.root_node, content, str(file_path))

    def extract_type_context(self, content: str, file_path: Path) -> TypeContext:
        """Extract type context from Go file."""
        context = TypeContext()

        if TREE_SITTER_AVAILABLE:
            symbols = self.extract_symbols(content, file_path)

            for symbol in symbols:
                if symbol.kind in ["function", "method"]:
                    context.functions[symbol.name] = ([], symbol.type_str)

        return context

    def extract_tests(self, content: str, file_path: Path) -> list[TestCase]:
        """Extract test cases from file."""
        if not TREE_SITTER_AVAILABLE:
            return []

        tree = self.parser.parse(bytes(content, "utf-8"))
        return self._detect_tests(tree.root_node, content, str(file_path))
