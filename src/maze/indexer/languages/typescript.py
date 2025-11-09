"""
TypeScript indexer for extracting symbols, types, and context.

This module provides TypeScript-specific code analysis using
tree-sitter and optional tsserver integration for type information.
"""

from __future__ import annotations

import json
import re
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
import logging

from maze.indexer.base import (
    BaseIndexer,
    Symbol,
    ImportInfo,
    TestCase,
    StyleInfo,
    IndexingResult,
)
from maze.core.types import (
    Type,
    TypeContext,
    FunctionSignature,
    TypeParameter,
    ClassType,
    InterfaceType,
)

logger = logging.getLogger(__name__)


class TypeScriptIndexer(BaseIndexer):
    """
    TypeScript/JavaScript code indexer.

    Extracts symbols, types, tests, and patterns from TypeScript
    and JavaScript codebases.
    """

    def __init__(self, project_path: Optional[Path] = None, use_tsserver: bool = False):
        """
        Initialize TypeScript indexer.

        Args:
            project_path: Root path of the project
            use_tsserver: Whether to use tsserver for type information
        """
        super().__init__(project_path)
        self.language = "typescript"
        self.file_extensions = {".ts", ".tsx", ".js", ".jsx", ".mts", ".cts"}
        self.use_tsserver = use_tsserver
        self.tsconfig_path = self._find_tsconfig()

    def index_file(self, file_path: Path) -> IndexingResult:
        """Index a single TypeScript/JavaScript file."""
        start_time = time.time()
        content = self.read_file(file_path)

        # Extract various components
        symbols = self.extract_symbols(content, file_path)
        imports = self.extract_imports(content, file_path)
        tests = self.extract_tests(content, file_path)
        style = self.extract_style(content)
        patterns = self.extract_patterns(symbols)

        # Extract JSON schemas from type definitions
        schemas = self._extract_schemas(content, file_path)

        duration_ms = (time.time() - start_time) * 1000

        return IndexingResult(
            symbols=symbols,
            imports=imports,
            tests=tests,
            style=style,
            files_processed=[str(file_path)],
            schemas=schemas,
            patterns=patterns,
            errors=[],
            duration_ms=duration_ms,
        )

    def index_directory(self, directory: Path) -> IndexingResult:
        """Index all TypeScript/JavaScript files in a directory."""
        files = self.find_files(directory)
        results = []

        for file_path in files:
            try:
                result = self.index_file(file_path)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to index {file_path}: {e}")
                # Create error result
                error_result = IndexingResult(
                    symbols=[],
                    imports=[],
                    tests=[],
                    style=StyleInfo(),
                    files_processed=[str(file_path)],
                    schemas=[],
                    patterns=[],
                    errors=[str(e)],
                    duration_ms=0.0,
                )
                results.append(error_result)

        return self.combine_results(results)

    def extract_symbols(self, content: str, file_path: Path) -> List[Symbol]:
        """Extract symbols from TypeScript/JavaScript content."""
        symbols = []
        lines = content.split('\n')

        for line_num, line in enumerate(lines, 1):
            line = line.strip()

            # Skip comments and empty lines
            if not line or line.startswith('//') or line.startswith('/*'):
                continue

            # Function declarations
            if match := re.match(r'(?:export\s+)?(?:async\s+)?function\s+(\w+)', line):
                symbols.append(Symbol(
                    name=match.group(1),
                    kind="function",
                    type_str=self._extract_function_type(line, lines[line_num:]),
                    file_path=str(file_path),
                    line=line_num,
                    column=line.index(match.group(1)),
                ))

            # Arrow functions assigned to const/let
            elif match := re.match(r'(?:export\s+)?(?:const|let)\s+(\w+)\s*=\s*(?:async\s+)?\(', line):
                symbols.append(Symbol(
                    name=match.group(1),
                    kind="function",
                    type_str=self._extract_arrow_function_type(line, lines[line_num:]),
                    file_path=str(file_path),
                    line=line_num,
                    column=line.index(match.group(1)),
                ))

            # Class declarations
            elif match := re.match(r'(?:export\s+)?(?:abstract\s+)?class\s+(\w+)', line):
                symbols.append(Symbol(
                    name=match.group(1),
                    kind="class",
                    type_str=match.group(1),
                    file_path=str(file_path),
                    line=line_num,
                    column=line.index(match.group(1)),
                ))

            # Interface declarations
            elif match := re.match(r'(?:export\s+)?interface\s+(\w+)', line):
                symbols.append(Symbol(
                    name=match.group(1),
                    kind="interface",
                    type_str=match.group(1),
                    file_path=str(file_path),
                    line=line_num,
                    column=line.index(match.group(1)),
                ))

            # Type aliases
            elif match := re.match(r'(?:export\s+)?type\s+(\w+)\s*=', line):
                symbols.append(Symbol(
                    name=match.group(1),
                    kind="type",
                    type_str=self._extract_type_alias(line, lines[line_num:]),
                    file_path=str(file_path),
                    line=line_num,
                    column=line.index(match.group(1)),
                ))

            # Enum declarations
            elif match := re.match(r'(?:export\s+)?enum\s+(\w+)', line):
                symbols.append(Symbol(
                    name=match.group(1),
                    kind="enum",
                    type_str=match.group(1),
                    file_path=str(file_path),
                    line=line_num,
                    column=line.index(match.group(1)),
                ))

            # Const/let/var declarations
            elif match := re.match(r'(?:export\s+)?(?:const|let|var)\s+(\w+)(?:\s*:\s*([^=]+))?\s*=', line):
                if not any(s.name == match.group(1) for s in symbols):  # Avoid duplicates with functions
                    type_str = match.group(2).strip() if match.group(2) else "any"
                    symbols.append(Symbol(
                        name=match.group(1),
                        kind="variable",
                        type_str=type_str,
                        file_path=str(file_path),
                        line=line_num,
                        column=line.index(match.group(1)),
                    ))

        # If tsserver is available, enhance with type information
        if self.use_tsserver:
            symbols = self._enhance_with_tsserver(symbols, file_path)

        return symbols

    def extract_type_context(self, content: str, file_path: Path) -> TypeContext:
        """Extract TypeContext from TypeScript content."""
        context = TypeContext(language="typescript")
        symbols = self.extract_symbols(content, file_path)

        for symbol in symbols:
            if symbol.kind == "variable":
                # Parse type string to Type object
                context.variables[symbol.name] = self._parse_type_string(symbol.type_str)

            elif symbol.kind == "function":
                # Parse function signature
                sig = self._parse_function_signature(symbol.name, symbol.type_str)
                if sig:
                    context.functions[symbol.name] = sig

            elif symbol.kind == "class":
                # Extract class properties and methods
                class_type = self._extract_class_type(content, symbol.name)
                if class_type:
                    context.classes[symbol.name] = class_type

            elif symbol.kind == "interface":
                # Extract interface properties and methods
                interface_type = self._extract_interface_type(content, symbol.name)
                if interface_type:
                    context.interfaces[symbol.name] = interface_type

            elif symbol.kind == "type":
                # Store type alias
                context.type_aliases[symbol.name] = self._parse_type_string(symbol.type_str)

        return context

    def extract_tests(self, content: str, file_path: Path) -> List[TestCase]:
        """Extract test cases from TypeScript/JavaScript content."""
        tests = []
        lines = content.split('\n')

        for line_num, line in enumerate(lines, 1):
            # Jest/Mocha style tests
            if match := re.match(r'(?:it|test|describe)\s*\(\s*[\'"`]([^\'"`]+)', line):
                test_name = match.group(1)
                tests.append(TestCase(
                    name=test_name,
                    kind="unit",
                    test_function=f"test_{line_num}",
                    file_path=str(file_path),
                    command=self._get_test_command(file_path),
                    tags=self._extract_test_tags(test_name),
                ))

            # Vitest style
            elif match := re.match(r'(?:expect|assert)\s*\(', line):
                # Look for containing test function
                test_name = self._find_containing_test(lines[:line_num])
                if test_name:
                    tests.append(TestCase(
                        name=test_name,
                        kind="unit",
                        test_function=f"test_{line_num}",
                        file_path=str(file_path),
                        command=self._get_test_command(file_path),
                    ))

        return tests

    def extract_imports(self, content: str, file_path: Path) -> List[ImportInfo]:
        """Extract import statements from TypeScript/JavaScript content."""
        imports = []
        lines = content.split('\n')

        for line_num, line in enumerate(lines, 1):
            line = line.strip()

            # ES6 imports
            if line.startswith('import '):
                # Named imports
                if match := re.match(r'import\s*\{([^}]+)\}\s*from\s*[\'"`]([^\'"`]+)', line):
                    symbols = [s.strip() for s in match.group(1).split(',')]
                    module = match.group(2)
                    imports.append(ImportInfo(
                        module=module,
                        symbols=symbols,
                        is_type_import='type ' in line,
                        file_path=str(file_path),
                        line=line_num,
                    ))

                # Default import
                elif match := re.match(r'import\s+(\w+)\s+from\s+[\'"`]([^\'"`]+)', line):
                    imports.append(ImportInfo(
                        module=match.group(2),
                        symbols=[match.group(1)],
                        is_type_import='type ' in line,
                        file_path=str(file_path),
                        line=line_num,
                    ))

                # Namespace import
                elif match := re.match(r'import\s*\*\s*as\s+(\w+)\s+from\s+[\'"`]([^\'"`]+)', line):
                    imports.append(ImportInfo(
                        module=match.group(2),
                        symbols=[],
                        alias=match.group(1),
                        is_type_import='type ' in line,
                        file_path=str(file_path),
                        line=line_num,
                    ))

            # CommonJS require
            elif 'require(' in line:
                if match := re.match(r'(?:const|let|var)\s+(\w+)\s*=\s*require\([\'"`]([^\'"`]+)', line):
                    imports.append(ImportInfo(
                        module=match.group(2),
                        symbols=[match.group(1)],
                        file_path=str(file_path),
                        line=line_num,
                    ))

        return imports

    # Private helper methods

    def _find_tsconfig(self) -> Optional[Path]:
        """Find tsconfig.json in project."""
        if self.project_path:
            tsconfig = self.project_path / "tsconfig.json"
            if tsconfig.exists():
                return tsconfig

            # Look in parent directories
            current = self.project_path.parent
            while current != current.parent:
                tsconfig = current / "tsconfig.json"
                if tsconfig.exists():
                    return tsconfig
                current = current.parent

        return None

    def _extract_function_type(self, line: str, following_lines: List[str]) -> str:
        """Extract function type signature."""
        # Look for return type
        if ':' in line and not '//' in line[:line.index(':') if ':' in line else len(line)]:
            # Has explicit return type
            if match := re.search(r'\)\s*:\s*([^{]+)', line):
                return_type = match.group(1).strip()
            else:
                return_type = "void"
        else:
            return_type = "any"

        # Extract parameters
        if match := re.search(r'\(([^)]*)\)', line):
            params = match.group(1)
        else:
            params = ""

        return f"({params}) => {return_type}"

    def _extract_arrow_function_type(self, line: str, following_lines: List[str]) -> str:
        """Extract arrow function type signature."""
        # Similar to regular function but for arrow syntax
        return self._extract_function_type(line, following_lines)

    def _extract_type_alias(self, line: str, following_lines: List[str]) -> str:
        """Extract type alias definition."""
        # Simple extraction - would need more complex parsing for multiline
        if '=' in line:
            return line[line.index('=') + 1:].strip().rstrip(';')
        return "unknown"

    def _parse_type_string(self, type_str: str) -> Type:
        """Parse TypeScript type string to Type object."""
        type_str = type_str.strip()

        # Handle nullable types
        nullable = type_str.endswith('?')
        if nullable:
            type_str = type_str[:-1].strip()

        # Handle union types (simplified)
        if '|' in type_str:
            # For now, take the first type
            type_str = type_str.split('|')[0].strip()

        # Handle generic types
        if match := re.match(r'(\w+)<(.+)>', type_str):
            base_type = match.group(1)
            param_str = match.group(2)
            # Simple parsing - would need proper parser for nested generics
            params = [self._parse_type_string(p.strip()) for p in param_str.split(',')]
            return Type(base_type, tuple(params), nullable)

        # Handle array notation
        if type_str.endswith('[]'):
            element_type = self._parse_type_string(type_str[:-2])
            return Type("Array", (element_type,), nullable)

        # Basic type
        return Type(type_str, nullable=nullable)

    def _parse_function_signature(self, name: str, type_str: str) -> Optional[FunctionSignature]:
        """Parse function type string to FunctionSignature."""
        # Simplified parsing - would need proper parser in production
        try:
            # Extract parameters and return type
            if '=>' in type_str:
                parts = type_str.split('=>')
                param_str = parts[0].strip()
                return_str = parts[1].strip()

                # Parse parameters (simplified)
                parameters = []
                if param_str.startswith('(') and param_str.endswith(')'):
                    param_str = param_str[1:-1]
                    if param_str:
                        for param in param_str.split(','):
                            param = param.strip()
                            if ':' in param:
                                param_name, param_type = param.split(':', 1)
                                param_name = param_name.strip().lstrip('?')
                                optional = '?' in param
                                parameters.append(TypeParameter(
                                    name=param_name,
                                    type=self._parse_type_string(param_type.strip()),
                                    optional=optional,
                                ))

                return FunctionSignature(
                    name=name,
                    parameters=parameters,
                    return_type=self._parse_type_string(return_str),
                )
        except Exception as e:
            logger.debug(f"Failed to parse function signature: {e}")

        return None

    def _extract_class_type(self, content: str, class_name: str) -> Optional[ClassType]:
        """Extract ClassType from content."""
        # Simplified extraction - would use AST in production
        # Look for class definition
        pattern = rf'class\s+{class_name}[^{{]*\{{([^}}]+)\}}'
        if match := re.search(pattern, content, re.DOTALL):
            class_body = match.group(1)

            properties = {}
            methods = {}

            # Extract properties and methods (simplified)
            for line in class_body.split('\n'):
                line = line.strip()
                if not line:
                    continue

                # Property
                if match := re.match(r'(\w+)\s*:\s*([^;]+);', line):
                    prop_name = match.group(1)
                    prop_type = match.group(2).strip()
                    properties[prop_name] = self._parse_type_string(prop_type)

                # Method (simplified)
                elif match := re.match(r'(?:async\s+)?(\w+)\s*\(', line):
                    method_name = match.group(1)
                    if method_name not in ('constructor', 'if', 'for', 'while'):
                        # Would parse full signature in production
                        methods[method_name] = FunctionSignature(
                            name=method_name,
                            parameters=[],
                            return_type=Type("any"),
                        )

            return ClassType(
                name=class_name,
                properties=properties,
                methods=methods,
            )

        return None

    def _extract_interface_type(self, content: str, interface_name: str) -> Optional[InterfaceType]:
        """Extract InterfaceType from content."""
        # Similar to class extraction
        pattern = rf'interface\s+{interface_name}[^{{]*\{{([^}}]+)\}}'
        if match := re.search(pattern, content, re.DOTALL):
            interface_body = match.group(1)

            properties = {}
            methods = {}

            for line in interface_body.split('\n'):
                line = line.strip()
                if not line:
                    continue

                # Property
                if match := re.match(r'(\w+)\??\s*:\s*([^;]+);', line):
                    prop_name = match.group(1)
                    prop_type = match.group(2).strip()
                    properties[prop_name] = self._parse_type_string(prop_type)

                # Method signature
                elif match := re.match(r'(\w+)\s*\([^)]*\)\s*:\s*([^;]+);', line):
                    method_name = match.group(1)
                    return_type = match.group(2).strip()
                    methods[method_name] = FunctionSignature(
                        name=method_name,
                        parameters=[],
                        return_type=self._parse_type_string(return_type),
                    )

            return InterfaceType(
                name=interface_name,
                properties=properties,
                methods=methods,
            )

        return None

    def _extract_schemas(self, content: str, file_path: Path) -> List[Dict[str, Any]]:
        """Extract JSON schemas from type definitions."""
        schemas = []

        # Look for Zod schemas
        if 'z.object(' in content:
            # Extract Zod schema definitions (simplified)
            pattern = r'const\s+(\w+Schema)\s*=\s*z\.object\((\{[^}]+\})\)'
            for match in re.finditer(pattern, content):
                schema_name = match.group(1)
                # Would parse Zod to JSON Schema in production
                schemas.append({
                    "name": schema_name,
                    "type": "object",
                    "source": "zod",
                })

        # Look for JSON Schema objects
        if '"$schema"' in content:
            # Extract literal JSON Schema definitions
            pattern = r'const\s+(\w+)\s*=\s*(\{[^}]*"\$schema"[^}]+\})'
            for match in re.finditer(pattern, content, re.DOTALL):
                schema_name = match.group(1)
                try:
                    schema_obj = json.loads(match.group(2))
                    schemas.append(schema_obj)
                except json.JSONDecodeError:
                    pass

        return schemas

    def _enhance_with_tsserver(self, symbols: List[Symbol], file_path: Path) -> List[Symbol]:
        """Enhance symbols with type information from tsserver."""
        # Would integrate with tsserver LSP in production
        # For now, return symbols as-is
        return symbols

    def _get_test_command(self, file_path: Path) -> str:
        """Get command to run tests for this file."""
        # Check for test runner
        if (self.project_path / "package.json").exists():
            # Check package.json for test script
            try:
                with open(self.project_path / "package.json") as f:
                    package = json.load(f)
                    if "scripts" in package and "test" in package["scripts"]:
                        return f"npm test -- {file_path}"
            except Exception:
                pass

        # Default commands for common test runners
        if file_path.name.endswith('.test.ts') or file_path.name.endswith('.spec.ts'):
            if (self.project_path / "vitest.config.ts").exists():
                return f"vitest {file_path}"
            elif (self.project_path / "jest.config.js").exists():
                return f"jest {file_path}"
            else:
                return f"npx jest {file_path}"

        return "npm test"

    def _extract_test_tags(self, test_name: str) -> List[str]:
        """Extract tags from test name."""
        tags = []

        # Common test categories
        if "unit" in test_name.lower():
            tags.append("unit")
        if "integration" in test_name.lower():
            tags.append("integration")
        if "e2e" in test_name.lower() or "end-to-end" in test_name.lower():
            tags.append("e2e")
        if "smoke" in test_name.lower():
            tags.append("smoke")
        if "regression" in test_name.lower():
            tags.append("regression")

        return tags

    def _find_containing_test(self, lines: List[str]) -> Optional[str]:
        """Find the test function containing a line."""
        # Search backwards for test definition
        for line in reversed(lines):
            if match := re.match(r'(?:it|test)\s*\(\s*[\'"`]([^\'"`]+)', line):
                return match.group(1)
        return None


# Export
__all__ = ["TypeScriptIndexer"]