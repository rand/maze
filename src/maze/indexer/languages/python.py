"""Python code indexer using AST parsing.

Extracts symbols, type hints, tests, and patterns from Python codebases.

Performance target: >1000 symbols/sec
"""

from __future__ import annotations

import ast
from pathlib import Path

from maze.core.types import TypeContext
from maze.indexer.base import (
    BaseIndexer,
    ImportInfo,
    IndexingResult,
    StyleInfo,
    Symbol,
    TestCase,
)


class PythonIndexer(BaseIndexer):
    """Python code indexer using AST parsing."""

    def __init__(self, project_path: Path | None = None):
        """Initialize Python indexer.

        Args:
            project_path: Root path of the project
        """
        super().__init__(project_path)
        self.language = "python"
        self.file_extensions = {".py", ".pyi"}

    def index_file(self, file_path: Path) -> IndexingResult:
        """Index a single Python file.

        Args:
            file_path: Path to Python file

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

            # Parse AST
            tree = ast.parse(content, filename=str(file_path))

            # Extract symbols
            symbols = self._extract_symbols_from_ast(tree, str(file_path))

            # Extract imports
            imports = self._extract_imports(tree, str(file_path))

            # Detect tests
            tests = self._detect_test_patterns(tree, str(file_path))

            # Detect style
            style = self._detect_style(content)

        except SyntaxError as e:
            errors.append(f"Syntax error in {file_path}: {e}")
            style = StyleInfo()
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
        """Index all Python files in directory.

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

        # Default style (will be refined from first file)
        combined_style = StyleInfo(indent_size=4, indent_type="space", quotes="single")

        # Find all Python files
        python_files = list(directory.rglob("*.py"))

        for file_path in python_files:
            # Skip __pycache__ and other excluded dirs
            if any(
                excluded in file_path.parts for excluded in ["__pycache__", ".git", "venv", ".venv"]
            ):
                continue

            result = self.index_file(file_path)

            all_symbols.extend(result.symbols)
            all_imports.extend(result.imports)
            all_tests.extend(result.tests)
            all_errors.extend(result.errors)
            all_files.extend(result.files_processed)

            # Use first file's style
            if file_path == python_files[0]:
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

    def _extract_symbols_from_ast(self, tree: ast.Module, file_path: str) -> list[Symbol]:
        """Extract symbols from AST.

        Args:
            tree: AST module
            file_path: Source file path

        Returns:
            List of extracted symbols
        """
        symbols = []

        for node in ast.walk(tree):
            # Functions and async functions
            if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                is_async = isinstance(node, ast.AsyncFunctionDef)
                kind = "async_function" if is_async else "function"

                # Extract return type
                return_type = self._extract_type_hint(node.returns) if node.returns else "Any"

                # Build function signature
                params = []
                for arg in node.args.args:
                    arg_type = self._extract_type_hint(arg.annotation) if arg.annotation else "Any"
                    params.append(f"{arg.arg}: {arg_type}")

                type_str = f"({', '.join(params)}) -> {return_type}"

                symbols.append(
                    Symbol(
                        name=node.name,
                        kind=kind,
                        type_str=type_str,
                        file_path=file_path,
                        line=node.lineno,
                        column=node.col_offset,
                        end_line=node.end_lineno,
                        end_column=node.end_col_offset,
                        docstring=ast.get_docstring(node),
                        metadata={
                            "is_async": is_async,
                            "decorators": [
                                d.id if isinstance(d, ast.Name) else str(d)
                                for d in node.decorator_list
                            ],
                        },
                    )
                )

            # Classes
            elif isinstance(node, ast.ClassDef):
                # Check if dataclass
                is_dataclass = any(
                    isinstance(d, ast.Name) and d.id == "dataclass" for d in node.decorator_list
                )

                symbols.append(
                    Symbol(
                        name=node.name,
                        kind="class",
                        type_str=f"class {node.name}",
                        file_path=file_path,
                        line=node.lineno,
                        column=node.col_offset,
                        end_line=node.end_lineno,
                        end_column=node.end_col_offset,
                        docstring=ast.get_docstring(node),
                        metadata={
                            "is_dataclass": is_dataclass,
                            "bases": [self._get_base_name(b) for b in node.bases],
                        },
                    )
                )

            # Variables with type annotations (PEP 526)
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                type_str = self._extract_type_hint(node.annotation)

                symbols.append(
                    Symbol(
                        name=node.target.id,
                        kind="variable",
                        type_str=type_str,
                        file_path=file_path,
                        line=node.lineno,
                        column=node.col_offset,
                    )
                )

        return symbols

    def _extract_type_hint(self, annotation: ast.AST | None) -> str:
        """Extract type hint as string.

        Args:
            annotation: AST annotation node

        Returns:
            Type hint string
        """
        if annotation is None:
            return "Any"

        # Handle different annotation types
        if isinstance(annotation, ast.Name):
            return annotation.id
        elif isinstance(annotation, ast.Constant):
            return str(annotation.value)
        elif isinstance(annotation, ast.Subscript):
            # Generic types: list[int], dict[str, Any]
            value = self._extract_type_hint(annotation.value)
            slice_val = self._extract_type_hint(annotation.slice)
            return f"{value}[{slice_val}]"
        elif isinstance(annotation, ast.Tuple):
            # Multiple subscript args: dict[str, int]
            elements = [self._extract_type_hint(e) for e in annotation.elts]
            return ", ".join(elements)
        elif isinstance(annotation, ast.BinOp) and isinstance(annotation.op, ast.BitOr):
            # Union types: int | str (PEP 604)
            left = self._extract_type_hint(annotation.left)
            right = self._extract_type_hint(annotation.right)
            return f"{left} | {right}"
        elif isinstance(annotation, ast.Attribute):
            # Module.Type (e.g., typing.Optional)
            return f"{self._extract_type_hint(annotation.value)}.{annotation.attr}"
        else:
            # Fallback: unparse if available
            try:
                return ast.unparse(annotation)
            except Exception:
                return "Any"

    def _extract_imports(self, tree: ast.Module, file_path: str) -> list[ImportInfo]:
        """Extract import statements.

        Args:
            tree: AST module
            file_path: Source file path

        Returns:
            List of imports
        """
        imports = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(
                        ImportInfo(
                            module=alias.name,
                            symbols=[],
                            alias=alias.asname,
                            file_path=file_path,
                            line=node.lineno,
                        )
                    )
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    symbols = [alias.name for alias in node.names]
                    imports.append(
                        ImportInfo(
                            module=node.module,
                            symbols=symbols,
                            file_path=file_path,
                            line=node.lineno,
                        )
                    )

        return imports

    def _detect_test_patterns(self, tree: ast.Module, file_path: str) -> list[TestCase]:
        """Detect test cases in code.

        Args:
            tree: AST module
            file_path: Source file path

        Returns:
            List of detected test cases
        """
        tests = []

        for node in ast.walk(tree):
            # pytest: test_* functions
            if isinstance(node, ast.FunctionDef):
                if node.name.startswith("test_"):
                    tests.append(
                        TestCase(
                            name=node.name,
                            kind="unit",
                            test_function=node.name,
                            file_path=file_path,
                            command=f"pytest {file_path}::{node.name}",
                        )
                    )

            # unittest: TestCase classes
            elif isinstance(node, ast.ClassDef):
                if any(self._get_base_name(base) == "TestCase" for base in node.bases):
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef) and item.name.startswith("test_"):
                            tests.append(
                                TestCase(
                                    name=f"{node.name}.{item.name}",
                                    kind="unit",
                                    test_function=item.name,
                                    file_path=file_path,
                                    command=f"pytest {file_path}::{node.name}::{item.name}",
                                )
                            )

        return tests

    def _detect_style(self, content: str) -> StyleInfo:
        """Detect code style from content.

        Args:
            content: File content

        Returns:
            Style information
        """
        # Detect indentation
        indent_size = 4  # Python standard
        indent_type = "space"

        # Detect quote preference
        single_quotes = content.count("'")
        double_quotes = content.count('"')
        quotes = "single" if single_quotes > double_quotes else "double"

        # Detect max line length
        lines = content.split("\n")
        max_line = max(len(line) for line in lines) if lines else 79
        max_line_length = min(max_line, 120)  # Cap at reasonable value

        return StyleInfo(
            indent_size=indent_size,
            indent_type=indent_type,
            quotes=quotes,
            semicolons=False,  # Python doesn't use semicolons
            max_line_length=max_line_length,
            naming_convention={
                "function": "snake_case",
                "class": "PascalCase",
                "variable": "snake_case",
                "constant": "UPPER_SNAKE_CASE",
            },
        )

    def _get_base_name(self, base: ast.AST) -> str:
        """Get base class name.

        Args:
            base: Base class AST node

        Returns:
            Base class name
        """
        if isinstance(base, ast.Name):
            return base.id
        elif isinstance(base, ast.Attribute):
            return base.attr
        else:
            return "Unknown"

    def extract_symbols(self, content: str, file_path: Path) -> list[Symbol]:
        """Extract symbols from file content.

        Args:
            content: File content
            file_path: Path to file

        Returns:
            List of symbols
        """
        try:
            tree = ast.parse(content, filename=str(file_path))
            return self._extract_symbols_from_ast(tree, str(file_path))
        except SyntaxError:
            return []

    def extract_type_context(self, content: str, file_path: Path) -> TypeContext:
        """Extract type context from file.

        Args:
            content: File content
            file_path: Path to file

        Returns:
            TypeContext with variables and functions
        """
        context = TypeContext()

        try:
            tree = ast.parse(content, filename=str(file_path))
            symbols = self._extract_symbols_from_ast(tree, str(file_path))

            for symbol in symbols:
                if symbol.kind == "variable":
                    context.variables[symbol.name] = symbol.type_str
                elif symbol.kind in ["function", "async_function"]:
                    # Parse function signature
                    context.functions[symbol.name] = ([], symbol.type_str)
        except SyntaxError:
            pass

        return context

    def extract_tests(self, content: str, file_path: Path) -> list[TestCase]:
        """Extract test cases from file.

        Args:
            content: File content
            file_path: Path to file

        Returns:
            List of test cases
        """
        try:
            tree = ast.parse(content, filename=str(file_path))
            return self._detect_test_patterns(tree, str(file_path))
        except SyntaxError:
            return []
