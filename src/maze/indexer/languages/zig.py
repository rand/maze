"""Zig code indexer using tree-sitter or basic parsing.

Extracts symbols, types, and patterns from Zig codebases.

Performance target: >1000 symbols/sec
"""

from __future__ import annotations

import re
from pathlib import Path

# Try to import tree-sitter-zig if available
try:
    from tree_sitter import Language, Node, Parser

    # Note: tree-sitter-zig may not be available, use fallback
    try:
        import tree_sitter_zig as ts_zig

        TREE_SITTER_AVAILABLE = True
    except ImportError:
        TREE_SITTER_AVAILABLE = False
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


class ZigIndexer(BaseIndexer):
    """Zig code indexer using regex-based parsing (fallback if tree-sitter unavailable)."""

    def __init__(self, project_path: Path | None = None):
        """Initialize Zig indexer.

        Args:
            project_path: Root path of the project
        """
        super().__init__(project_path)
        self.language = "zig"
        self.file_extensions = {".zig"}

        if TREE_SITTER_AVAILABLE:
            self.ts_language = Language(ts_zig.language())
            self.parser = Parser(self.ts_language)
        else:
            self.parser = None

    def index_file(self, file_path: Path) -> IndexingResult:
        """Index a single Zig file.

        Args:
            file_path: Path to Zig file

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

            # Use regex-based extraction (fallback approach)
            symbols = self._extract_symbols_regex(content, str(file_path))
            imports = self._extract_imports_regex(content, str(file_path))
            tests = self._detect_tests_regex(content, str(file_path))
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
        """Index all Zig files in directory.

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

        combined_style = StyleInfo(indent_size=4, indent_type="space")

        zig_files = list(directory.rglob("*.zig"))

        for file_path in zig_files:
            if "zig-cache" in file_path.parts or "zig-out" in file_path.parts:
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

    def _extract_symbols_regex(self, content: str, file_path: str) -> list[Symbol]:
        """Extract symbols using regex patterns.

        Args:
            content: File content
            file_path: File path

        Returns:
            List of symbols
        """
        symbols = []

        # Function pattern: pub fn name(...) type
        fn_pattern = r"(pub\s+)?fn\s+(\w+)\s*\([^)]*\)\s*([^{]+)?"
        for match in re.finditer(fn_pattern, content):
            is_pub = match.group(1) is not None
            name = match.group(2)
            return_type = match.group(3).strip() if match.group(3) else "void"

            line = content[: match.start()].count("\n") + 1

            symbols.append(
                Symbol(
                    name=name,
                    kind="function",
                    type_str=f"fn {name}",
                    file_path=file_path,
                    line=line,
                    column=0,
                    metadata={"is_pub": is_pub, "return_type": return_type},
                )
            )

        # Struct pattern: pub const Name = struct
        struct_pattern = r"(pub\s+)?const\s+(\w+)\s*=\s*struct"
        for match in re.finditer(struct_pattern, content):
            is_pub = match.group(1) is not None
            name = match.group(2)

            line = content[: match.start()].count("\n") + 1

            symbols.append(
                Symbol(
                    name=name,
                    kind="struct",
                    type_str=f"struct {name}",
                    file_path=file_path,
                    line=line,
                    column=0,
                    metadata={"is_pub": is_pub},
                )
            )

        # Enum pattern: pub const Name = enum
        enum_pattern = r"(pub\s+)?const\s+(\w+)\s*=\s*enum"
        for match in re.finditer(enum_pattern, content):
            is_pub = match.group(1) is not None
            name = match.group(2)

            line = content[: match.start()].count("\n") + 1

            symbols.append(
                Symbol(
                    name=name,
                    kind="enum",
                    type_str=f"enum {name}",
                    file_path=file_path,
                    line=line,
                    column=0,
                    metadata={"is_pub": is_pub},
                )
            )

        return symbols

    def _extract_imports_regex(self, content: str, file_path: str) -> list[ImportInfo]:
        """Extract imports using regex."""
        imports = []

        # Import pattern: const name = @import("path")
        import_pattern = r'const\s+(\w+)\s*=\s*@import\("([^"]+)"\)'
        for match in re.finditer(import_pattern, content):
            alias = match.group(1)
            module = match.group(2)
            line = content[: match.start()].count("\n") + 1

            imports.append(
                ImportInfo(
                    module=module,
                    symbols=[],
                    alias=alias,
                    file_path=file_path,
                    line=line,
                )
            )

        return imports

    def _detect_tests_regex(self, content: str, file_path: str) -> list[TestCase]:
        """Detect test functions (test "name" pattern)."""
        tests = []

        # Test pattern: test "test name" { }
        test_pattern = r'test\s+"([^"]+)"'
        for match in re.finditer(test_pattern, content):
            test_name = match.group(1)
            line = content[: match.start()].count("\n") + 1

            tests.append(
                TestCase(
                    name=test_name,
                    kind="unit",
                    test_function=test_name,
                    file_path=file_path,
                    command=f"zig test {file_path}",
                )
            )

        return tests

    def _detect_style(self, content: str) -> StyleInfo:
        """Detect Zig code style."""
        return StyleInfo(
            indent_size=4,
            indent_type="space",
            quotes="double",
            semicolons=True,
            max_line_length=100,
            naming_convention={
                "function": "camelCase",
                "struct": "PascalCase",
                "enum": "PascalCase",
                "variable": "snake_case",
                "constant": "UPPER_SNAKE_CASE",
            },
        )

    def extract_symbols(self, content: str, file_path: Path) -> list[Symbol]:
        """Extract symbols from file content."""
        return self._extract_symbols_regex(content, str(file_path))

    def extract_type_context(self, content: str, file_path: Path) -> TypeContext:
        """Extract type context from Zig file."""
        context = TypeContext()
        symbols = self.extract_symbols(content, file_path)

        for symbol in symbols:
            if symbol.kind == "function":
                context.functions[symbol.name] = ([], symbol.type_str)

        return context

    def extract_tests(self, content: str, file_path: Path) -> list[TestCase]:
        """Extract test cases from file."""
        return self._detect_tests_regex(content, str(file_path))
