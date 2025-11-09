"""
Base indexer interface for extracting context from codebases.

This module defines the abstract interface that all language-specific
indexers must implement to extract symbols, types, schemas, and patterns
from source code.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
import logging
import json
import hashlib
from datetime import datetime

from maze.core.types import (
    Type,
    TypeContext,
    FunctionSignature,
    ClassType,
    InterfaceType,
    IndexedContext,
)

logger = logging.getLogger(__name__)


@dataclass
class Symbol:
    """Represents a symbol extracted from code."""
    name: str
    kind: str  # variable, function, class, interface, type, enum
    type_str: str  # String representation of type
    file_path: str
    line: int
    column: int
    end_line: Optional[int] = None
    end_column: Optional[int] = None
    docstring: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "kind": self.kind,
            "type": self.type_str,
            "location": {
                "file": self.file_path,
                "line": self.line,
                "column": self.column,
                "end_line": self.end_line,
                "end_column": self.end_column,
            },
            "docstring": self.docstring,
            "metadata": self.metadata,
        }


@dataclass
class ImportInfo:
    """Information about an import statement."""
    module: str
    symbols: List[str]  # Specific symbols imported
    alias: Optional[str] = None
    is_type_import: bool = False
    file_path: str = ""
    line: int = 0


@dataclass
class TestCase:
    """Represents a test case found in the code."""
    name: str
    kind: str  # unit, integration, e2e, property
    test_function: str
    file_path: str
    command: Optional[str] = None  # Command to run this test
    tags: List[str] = field(default_factory=list)


@dataclass
class StyleInfo:
    """Code style information extracted from the codebase."""
    indent_size: int = 2
    indent_type: str = "space"  # space or tab
    quotes: str = "double"  # single, double, or backtick
    semicolons: bool = True
    max_line_length: int = 100
    naming_convention: Dict[str, str] = field(default_factory=dict)  # e.g., {"function": "camelCase"}


@dataclass
class IndexingResult:
    """Complete result from indexing a codebase."""
    symbols: List[Symbol]
    imports: List[ImportInfo]
    tests: List[TestCase]
    style: StyleInfo
    files_processed: List[str]
    schemas: List[Dict[str, Any]]  # JSON schemas found
    patterns: List[str]  # Common patterns detected
    errors: List[str]  # Any errors during indexing
    duration_ms: float
    timestamp: datetime = field(default_factory=datetime.now)

    def to_indexed_context(self, language: str, project_path: Optional[str] = None) -> IndexedContext:
        """Convert to IndexedContext for use in constraint synthesis."""
        return IndexedContext(
            files=[{"path": f, "lang": language} for f in self.files_processed],
            symbols=[s.to_dict() for s in self.symbols],
            schemas=self.schemas,
            style=self.style.__dict__,
            tests=[
                {
                    "name": t.name,
                    "kind": t.kind,
                    "cmd": t.command or f"test {t.name}"
                }
                for t in self.tests
            ],
            constraints_candidates=self._extract_constraint_candidates(),
            language=language,
            project_path=project_path,
            indexed_at=self.timestamp,
        )

    def _extract_constraint_candidates(self) -> List[Dict[str, Any]]:
        """Extract potential constraints from the indexed data."""
        candidates = []

        # Extract enum-like constants
        constants_by_prefix = {}
        for symbol in self.symbols:
            if symbol.kind == "variable" and symbol.name.isupper():
                prefix = symbol.name.split('_')[0] if '_' in symbol.name else symbol.name
                if prefix not in constants_by_prefix:
                    constants_by_prefix[prefix] = []
                constants_by_prefix[prefix].append(symbol.name)

        for prefix, constants in constants_by_prefix.items():
            if len(constants) > 1:
                candidates.append({
                    "kind": "enum",
                    "name": prefix,
                    "values": constants,
                })

        # Extract numeric bounds from variable names
        for symbol in self.symbols:
            if "max" in symbol.name.lower() or "min" in symbol.name.lower():
                candidates.append({
                    "kind": "numeric_bound",
                    "symbol": symbol.name,
                    "type": "max" if "max" in symbol.name.lower() else "min",
                })

        return candidates


class BaseIndexer(ABC):
    """
    Abstract base class for language-specific code indexers.

    Subclasses must implement the indexing logic for specific languages,
    extracting symbols, types, tests, and other relevant information.
    """

    def __init__(self, project_path: Optional[Path] = None):
        """
        Initialize indexer.

        Args:
            project_path: Root path of the project to index
        """
        self.project_path = Path(project_path) if project_path else Path.cwd()
        self.file_extensions: Set[str] = set()
        self.language: str = "unknown"
        self._file_cache: Dict[str, str] = {}

    @abstractmethod
    def index_file(self, file_path: Path) -> IndexingResult:
        """
        Index a single file.

        Args:
            file_path: Path to the file to index

        Returns:
            IndexingResult containing extracted information
        """
        pass

    @abstractmethod
    def index_directory(self, directory: Path) -> IndexingResult:
        """
        Index all relevant files in a directory.

        Args:
            directory: Path to directory to index

        Returns:
            Combined IndexingResult for all files
        """
        pass

    @abstractmethod
    def extract_symbols(self, content: str, file_path: Path) -> List[Symbol]:
        """
        Extract symbols from file content.

        Args:
            content: File content
            file_path: Path to the file

        Returns:
            List of extracted symbols
        """
        pass

    @abstractmethod
    def extract_type_context(self, content: str, file_path: Path) -> TypeContext:
        """
        Extract type context from file content.

        Args:
            content: File content
            file_path: Path to the file

        Returns:
            TypeContext with available types and functions
        """
        pass

    @abstractmethod
    def extract_tests(self, content: str, file_path: Path) -> List[TestCase]:
        """
        Extract test cases from file content.

        Args:
            content: File content
            file_path: Path to the file

        Returns:
            List of test cases found
        """
        pass

    def extract_imports(self, content: str, file_path: Path) -> List[ImportInfo]:
        """
        Extract import statements from file content.

        Default implementation - can be overridden by subclasses.

        Args:
            content: File content
            file_path: Path to the file

        Returns:
            List of import information
        """
        imports = []
        lines = content.split('\n')

        for i, line in enumerate(lines):
            line = line.strip()

            # Common import patterns across languages
            if line.startswith('import '):
                # JS/TS/Python style
                parts = line[7:].strip()
                imports.append(ImportInfo(
                    module=parts.split()[0],
                    symbols=[],
                    file_path=str(file_path),
                    line=i + 1
                ))
            elif line.startswith('from '):
                # Python style
                if ' import ' in line:
                    module = line[5:line.index(' import ')].strip()
                    symbols_str = line[line.index(' import ') + 8:].strip()
                    symbols = [s.strip() for s in symbols_str.split(',')]
                    imports.append(ImportInfo(
                        module=module,
                        symbols=symbols,
                        file_path=str(file_path),
                        line=i + 1
                    ))

        return imports

    def extract_style(self, content: str) -> StyleInfo:
        """
        Extract code style information from content.

        Default implementation - can be overridden by subclasses.

        Args:
            content: File content

        Returns:
            Style information
        """
        style = StyleInfo()
        lines = content.split('\n')

        if lines:
            # Detect indentation
            for line in lines:
                if line and line[0] in (' ', '\t'):
                    if line[0] == '\t':
                        style.indent_type = "tab"
                        style.indent_size = 1
                    else:
                        # Count leading spaces
                        spaces = len(line) - len(line.lstrip())
                        if spaces > 0:
                            style.indent_size = min(spaces, 4)
                    break

            # Detect quotes
            single_quotes = content.count("'")
            double_quotes = content.count('"')
            backticks = content.count('`')

            if backticks > max(single_quotes, double_quotes):
                style.quotes = "backtick"
            elif single_quotes > double_quotes:
                style.quotes = "single"
            else:
                style.quotes = "double"

            # Detect semicolons (for JS/TS)
            if self.language in ("javascript", "typescript"):
                # Check if lines end with semicolons
                code_lines = [l.strip() for l in lines if l.strip() and not l.strip().startswith('//')]
                if code_lines:
                    with_semicolon = sum(1 for l in code_lines if l.endswith(';'))
                    style.semicolons = with_semicolon > len(code_lines) // 2

            # Detect max line length
            if lines:
                style.max_line_length = max(len(line) for line in lines)

        return style

    def extract_patterns(self, symbols: List[Symbol]) -> List[str]:
        """
        Extract common patterns from symbols.

        Args:
            symbols: List of symbols

        Returns:
            List of detected patterns
        """
        patterns = []

        # Look for common prefixes/suffixes
        function_names = [s.name for s in symbols if s.kind == "function"]

        # Check for async pattern
        async_count = sum(1 for name in function_names if name.startswith("async") or "Async" in name)
        if async_count > len(function_names) // 3:
            patterns.append("async-heavy")

        # Check for test pattern
        test_count = sum(1 for name in function_names if "test" in name.lower() or "spec" in name.lower())
        if test_count > 0:
            patterns.append("has-tests")

        # Check for getter/setter pattern
        getter_count = sum(1 for name in function_names if name.startswith("get") or name.startswith("set"))
        if getter_count > len(function_names) // 4:
            patterns.append("getter-setter")

        return patterns

    def find_files(self, directory: Path, extensions: Optional[Set[str]] = None) -> List[Path]:
        """
        Find all files with relevant extensions in a directory.

        Args:
            directory: Directory to search
            extensions: File extensions to look for (uses self.file_extensions if None)

        Returns:
            List of file paths
        """
        if extensions is None:
            extensions = self.file_extensions

        files = []
        for ext in extensions:
            files.extend(directory.rglob(f"*{ext}"))

        # Filter out common directories to ignore
        ignore_dirs = {"node_modules", ".git", "__pycache__", "dist", "build", ".next", "target"}
        files = [f for f in files if not any(ignore in f.parts for ignore in ignore_dirs)]

        return sorted(files)

    def read_file(self, file_path: Path) -> str:
        """
        Read file content with caching.

        Args:
            file_path: Path to file

        Returns:
            File content
        """
        path_str = str(file_path)
        if path_str in self._file_cache:
            return self._file_cache[path_str]

        try:
            content = file_path.read_text(encoding='utf-8')
            self._file_cache[path_str] = content
            return content
        except Exception as e:
            logger.error(f"Failed to read {file_path}: {e}")
            return ""

    def combine_results(self, results: List[IndexingResult]) -> IndexingResult:
        """
        Combine multiple indexing results into one.

        Args:
            results: List of IndexingResult objects

        Returns:
            Combined IndexingResult
        """
        if not results:
            return IndexingResult(
                symbols=[],
                imports=[],
                tests=[],
                style=StyleInfo(),
                files_processed=[],
                schemas=[],
                patterns=[],
                errors=[],
                duration_ms=0.0
            )

        combined = IndexingResult(
            symbols=[],
            imports=[],
            tests=[],
            style=results[0].style if results else StyleInfo(),
            files_processed=[],
            schemas=[],
            patterns=[],
            errors=[],
            duration_ms=0.0
        )

        for result in results:
            combined.symbols.extend(result.symbols)
            combined.imports.extend(result.imports)
            combined.tests.extend(result.tests)
            combined.files_processed.extend(result.files_processed)
            combined.schemas.extend(result.schemas)
            combined.patterns.extend(result.patterns)
            combined.errors.extend(result.errors)
            combined.duration_ms += result.duration_ms

        # Deduplicate patterns
        combined.patterns = list(set(combined.patterns))

        return combined

    def cache_key(self, content: str) -> str:
        """Generate cache key for content."""
        return hashlib.sha256(content.encode()).hexdigest()[:16]


# Export main interfaces
__all__ = [
    "BaseIndexer",
    "Symbol",
    "ImportInfo",
    "TestCase",
    "StyleInfo",
    "IndexingResult",
]