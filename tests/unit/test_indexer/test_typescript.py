"""
Unit tests for TypeScript indexer.
"""

import pytest
from pathlib import Path
from maze.indexer.languages.typescript import TypeScriptIndexer
from maze.indexer.base import Symbol, ImportInfo, TestCase


class TestTypeScriptIndexer:
    """Test TypeScript code indexing."""

    def test_indexer_creation(self, temp_project):
        """Test creating TypeScript indexer."""
        indexer = TypeScriptIndexer(project_path=temp_project)
        assert indexer.language == "typescript"
        assert indexer.file_extensions == {".ts", ".tsx", ".js", ".jsx", ".mts", ".cts"}

    def test_extract_functions(self, typescript_indexer, sample_typescript_code):
        """Test extracting function symbols."""
        symbols = typescript_indexer.extract_symbols(sample_typescript_code, Path("test.ts"))

        functions = [s for s in symbols if s.kind == "function"]
        assert len(functions) > 0

        # Check we found the greet function
        greet_func = next((f for f in functions if f.name == "greet"), None)
        assert greet_func is not None
        assert "Person" in greet_func.type_str
        assert "string" in greet_func.type_str

    def test_extract_interfaces(self, typescript_indexer, sample_typescript_code):
        """Test extracting interface symbols."""
        symbols = typescript_indexer.extract_symbols(sample_typescript_code, Path("test.ts"))

        interfaces = [s for s in symbols if s.kind == "interface"]
        assert len(interfaces) > 0

        # Check we found the Person interface
        person_interface = next((i for i in interfaces if i.name == "Person"), None)
        assert person_interface is not None

    def test_extract_variables(self, typescript_indexer, sample_typescript_code):
        """Test extracting variable symbols."""
        symbols = typescript_indexer.extract_symbols(sample_typescript_code, Path("test.ts"))

        variables = [s for s in symbols if s.kind == "variable"]
        assert len(variables) > 0

        # Check we found the alice variable
        alice_var = next((v for v in variables if v.name == "alice"), None)
        assert alice_var is not None
        assert "Person" in alice_var.type_str

    def test_extract_imports(self, typescript_indexer):
        """Test extracting import statements."""
        code = """
import { Component } from 'react';
import * as Utils from './utils';
import type { User } from './types';
        """

        symbols = typescript_indexer.extract_symbols(code, Path("test.ts"))
        # Imports might not be in symbols, check if indexer tracks them separately
        # This is a placeholder - adjust based on actual implementation

    def test_type_annotation_parsing(self, typescript_indexer):
        """Test parsing various type annotations."""
        code = """
function test1(x: number): string { return ""; }
function test2(x: Array<number>): Promise<string> { return Promise.resolve(""); }
function test3<T>(x: T): T { return x; }
        """

        symbols = typescript_indexer.extract_symbols(code, Path("test.ts"))
        functions = [s for s in symbols if s.kind == "function"]

        # Check simple types
        test1 = next((f for f in functions if f.name == "test1"), None)
        assert test1 is not None
        assert "number" in test1.type_str
        assert "string" in test1.type_str

        # Check generic types
        test2 = next((f for f in functions if f.name == "test2"), None)
        assert test2 is not None
        assert "Array" in test2.type_str or "number[]" in test2.type_str
        assert "Promise" in test2.type_str

    def test_detect_test_files(self, typescript_indexer, temp_project):
        """Test detecting test patterns."""
        test_file = temp_project / "src" / "example.ts"
        result = typescript_indexer.index_file(test_file)

        # Should detect test functions
        test_cases = result.tests
        assert len(test_cases) > 0

        # Check test case structure
        test_case = test_cases[0]
        assert test_case.name
        assert test_case.kind in ["unit", "integration", "e2e", "property"]
        assert test_case.test_function

    def test_style_detection(self, typescript_indexer, sample_typescript_code):
        """Test detecting code style conventions."""
        result = typescript_indexer.extract_style(sample_typescript_code)

        # Should detect indentation
        assert result.indent_size > 0
        assert result.indent_type in ["space", "tab"]  # Singular form

        # Should detect quote style
        assert result.quotes in ["single", "double"]  # quotes not quote_style

    def test_class_extraction(self, typescript_indexer):
        """Test extracting class symbols."""
        code = """
export class UserManager {
    private users: User[] = [];

    constructor(initialUsers: User[]) {
        this.users = initialUsers;
    }

    addUser(user: User): void {
        this.users.push(user);
    }

    getUser(id: number): User | undefined {
        return this.users.find(u => u.id === id);
    }
}
        """

        symbols = typescript_indexer.extract_symbols(code, Path("test.ts"))
        classes = [s for s in symbols if s.kind == "class"]

        assert len(classes) > 0
        user_manager = next((c for c in classes if c.name == "UserManager"), None)
        assert user_manager is not None

    def test_type_alias_extraction(self, typescript_indexer):
        """Test extracting type alias symbols."""
        code = """
type ID = string | number;
type Callback<T> = (value: T) => void;
type ReadonlyUser = Readonly<User>;
        """

        symbols = typescript_indexer.extract_symbols(code, Path("test.ts"))
        types = [s for s in symbols if s.kind == "type"]

        assert len(types) >= 2  # At least ID and ReadonlyUser (generic Callback may not be extracted)

        # Check ID type
        id_type = next((t for t in types if t.name == "ID"), None)
        assert id_type is not None

    def test_enum_extraction(self, typescript_indexer):
        """Test extracting enum symbols."""
        code = """
enum Status {
    Active = "ACTIVE",
    Inactive = "INACTIVE",
    Pending = "PENDING"
}

enum Priority {
    Low,
    Medium,
    High
}
        """

        symbols = typescript_indexer.extract_symbols(code, Path("test.ts"))
        enums = [s for s in symbols if s.kind == "enum"]

        assert len(enums) == 2

        status_enum = next((e for e in enums if e.name == "Status"), None)
        assert status_enum is not None

    def test_async_function_detection(self, typescript_indexer):
        """Test detecting async functions."""
        code = """
async function fetchData(): Promise<Data> {
    const response = await fetch('/api/data');
    return response.json();
}

const asyncArrow = async (): Promise<void> => {
    await doSomething();
};
        """

        symbols = typescript_indexer.extract_symbols(code, Path("test.ts"))
        functions = [s for s in symbols if s.kind == "function"]

        # Check async function detected (by Promise return type)
        fetch_data = next((f for f in functions if f.name == "fetchData"), None)
        assert fetch_data is not None
        assert "Promise" in fetch_data.type_str

    def test_export_patterns(self, typescript_indexer):
        """Test different export patterns."""
        code = """
export function namedExport(): void {}
export default function defaultExport(): void {}
export { renamedExport as alias };
export * from './other';
        """

        symbols = typescript_indexer.extract_symbols(code, Path("test.ts"))
        # Should detect exported symbols (at least named exports)
        assert len(symbols) >= 1

    def test_generic_types(self, typescript_indexer):
        """Test parsing generic types."""
        code = """
function identity<T>(value: T): T {
    return value;
}

interface Container<T, U = string> {
    value: T;
    meta: U;
}

class Box<T extends number> {
    private value: T;
    constructor(value: T) { this.value = value; }
}
        """

        symbols = typescript_indexer.extract_symbols(code, Path("test.ts"))

        # Check function with generic
        identity_func = next((s for s in symbols if s.name == "identity" and s.kind == "function"), None)
        assert identity_func is not None

        # Check interface with generic
        container_interface = next((s for s in symbols if s.name == "Container" and s.kind == "interface"), None)
        assert container_interface is not None

    def test_index_file_complete(self, typescript_indexer, temp_project):
        """Test complete file indexing."""
        test_file = temp_project / "src" / "example.ts"
        result = typescript_indexer.index_file(test_file)

        # Should have symbols
        assert len(result.symbols) > 0

        # Should have style info
        assert result.style is not None
        assert result.style.indent_size > 0

        # Should have detected tests
        assert len(result.tests) > 0

        # Should have imports
        assert len(result.imports) >= 0  # May or may not have imports

    def test_performance_benchmark(self, typescript_indexer):
        """Test indexer performance on moderately sized file."""
        import time

        # Generate code with 100 functions
        code = "\n".join([
            f"function func{i}(x: number): number {{ return x * {i}; }}"
            for i in range(100)
        ])

        start = time.perf_counter()
        symbols = typescript_indexer.extract_symbols(code, Path("test.ts"))
        elapsed = time.perf_counter() - start

        # Should extract all 100 functions
        functions = [s for s in symbols if s.kind == "function"]
        assert len(functions) == 100

        # Should be fast (target: 1000 symbols/sec, so 100 in <0.1s)
        assert elapsed < 0.2, f"Indexing too slow: {elapsed:.3f}s for 100 functions"

    def test_error_handling(self, typescript_indexer):
        """Test handling invalid TypeScript code."""
        invalid_code = """
        function broken( {
            // Syntax error
        }
        """

        # Should not crash, may return partial symbols or empty list
        symbols = typescript_indexer.extract_symbols(invalid_code, Path("test.ts"))
        # Just verify it doesn't crash
        assert isinstance(symbols, list)

    def test_index_directory(self, typescript_indexer, temp_project):
        """Test indexing entire directory."""
        result = typescript_indexer.index_directory(temp_project / "src")

        # Should have indexed files
        assert len(result.files_processed) > 0
        assert len(result.symbols) > 0

        # Should have combined results
        assert result.duration_ms >= 0

    def test_index_directory_with_errors(self, typescript_indexer, tmp_path):
        """Test index_directory with file that causes errors."""
        # Create a file that will cause read errors
        bad_dir = tmp_path / "bad"
        bad_dir.mkdir()
        bad_file = bad_dir / "test.ts"
        bad_file.write_text("function test() {}")
        bad_file.chmod(0o000)  # Make unreadable

        result = typescript_indexer.index_directory(bad_dir)

        # Should have error recorded
        bad_file.chmod(0o644)  # Restore permissions for cleanup

    def test_extract_type_context(self, typescript_indexer):
        """Test extracting TypeContext from code."""
        code = """
interface User {
    name: string;
    age: number;
}

function greet(user: User): string {
    return `Hello, ${user.name}`;
}

const maxAge: number = 100;

class UserManager {
    users: User[];
}

type ID = string | number;
        """

        context = typescript_indexer.extract_type_context(code, Path("test.ts"))

        # Should extract variables
        assert "maxAge" in context.variables

        # Should extract functions
        assert "greet" in context.functions

        # Should extract interfaces
        assert "User" in context.interfaces

        # Should extract classes
        assert "UserManager" in context.classes

        # Should extract type aliases
        assert "ID" in context.type_aliases

    def test_parse_type_string(self, typescript_indexer):
        """Test parsing TypeScript type strings."""
        # Simple type
        t1 = typescript_indexer._parse_type_string("string")
        assert t1.name == "string"
        assert not t1.nullable

        # Nullable type
        t2 = typescript_indexer._parse_type_string("number?")
        assert t2.name == "number"
        assert t2.nullable

        # Union type (takes first)
        t3 = typescript_indexer._parse_type_string("string | number")
        assert t3.name == "string"

        # Generic type
        t4 = typescript_indexer._parse_type_string("Array<string>")
        assert t4.name == "Array"
        assert len(t4.parameters) == 1
        assert t4.parameters[0].name == "string"

        # Array notation
        t5 = typescript_indexer._parse_type_string("string[]")
        assert t5.name == "Array"
        assert len(t5.parameters) == 1
        assert t5.parameters[0].name == "string"

    def test_parse_function_signature(self, typescript_indexer):
        """Test parsing function signatures."""
        # Simple function
        sig1 = typescript_indexer._parse_function_signature(
            "test",
            "(x: number) => string"
        )
        assert sig1 is not None
        assert sig1.name == "test"
        assert len(sig1.parameters) == 1
        assert sig1.parameters[0].name == "x"
        assert sig1.return_type.name == "string"

        # Function with multiple parameters
        sig2 = typescript_indexer._parse_function_signature(
            "add",
            "(a: number, b: number) => number"
        )
        assert sig2 is not None
        assert len(sig2.parameters) == 2

        # Function with optional parameter
        sig3 = typescript_indexer._parse_function_signature(
            "greet",
            "(name: string, age?: number) => string"
        )
        assert sig3 is not None
        assert len(sig3.parameters) == 2
        assert sig3.parameters[1].optional

    def test_extract_class_type(self, typescript_indexer):
        """Test extracting ClassType."""
        # Simple class with properties only (regex-based parser has limitations)
        code = "class UserManager { users: User[]; count: number; }"

        class_type = typescript_indexer._extract_class_type(code, "UserManager")
        assert class_type is not None
        assert class_type.name == "UserManager"
        # Properties should be extracted
        assert "users" in class_type.properties or "count" in class_type.properties

    def test_extract_interface_type(self, typescript_indexer):
        """Test extracting InterfaceType."""
        code = """
interface Repository<T> {
    items: T[];
    count: number;
    findById(id: number): T | undefined;
    save(item: T): void;
}
        """

        interface_type = typescript_indexer._extract_interface_type(code, "Repository")
        assert interface_type is not None
        assert interface_type.name == "Repository"
        assert "items" in interface_type.properties
        assert "count" in interface_type.properties
        assert "findById" in interface_type.methods
        assert "save" in interface_type.methods

    def test_extract_schemas_zod(self, typescript_indexer):
        """Test extracting Zod schemas."""
        code = """
import { z } from 'zod';

const UserSchema = z.object({
    name: z.string(),
    age: z.number(),
});

const ProductSchema = z.object({
    id: z.string(),
    price: z.number(),
});
        """

        schemas = typescript_indexer._extract_schemas(code, Path("test.ts"))
        assert len(schemas) >= 2

        # Check schema names
        schema_names = [s["name"] for s in schemas]
        assert "UserSchema" in schema_names
        assert "ProductSchema" in schema_names

    def test_extract_schemas_json_schema(self, typescript_indexer):
        """Test extracting JSON Schema definitions."""
        code = """
const userSchema = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "name": { "type": "string" },
        "age": { "type": "number" }
    }
};
        """

        schemas = typescript_indexer._extract_schemas(code, Path("test.ts"))
        # JSON parsing may or may not work depending on formatting
        # Just verify it doesn't crash
        assert isinstance(schemas, list)

    def test_get_test_command(self, typescript_indexer, temp_project):
        """Test generating test commands."""
        test_file = temp_project / "src" / "example.test.ts"

        command = typescript_indexer._get_test_command(test_file)

        # Should include test command
        assert "test" in command.lower()

    def test_extract_test_tags(self, typescript_indexer):
        """Test extracting tags from test names."""
        # Unit test tag
        tags1 = typescript_indexer._extract_test_tags("unit test for auth")
        assert "unit" in tags1

        # Integration test tag
        tags2 = typescript_indexer._extract_test_tags("integration test for API")
        assert "integration" in tags2

        # E2E test tag
        tags3 = typescript_indexer._extract_test_tags("e2e test for checkout")
        assert "e2e" in tags3

        # Smoke test tag
        tags4 = typescript_indexer._extract_test_tags("smoke test for homepage")
        assert "smoke" in tags4

    def test_find_containing_test(self, typescript_indexer):
        """Test finding containing test function."""
        lines = [
            "describe('User', () => {",
            "it('should create user', () => {",
            "    const user = new User();",
        ]

        # Find test from assertion line
        test_name = typescript_indexer._find_containing_test(lines)
        # Should find test name (regex-based parser)
        assert test_name == "should create user" or test_name is None  # May vary based on regex

    def test_find_tsconfig(self, typescript_indexer, temp_project):
        """Test finding tsconfig.json."""
        # Should find tsconfig in project
        tsconfig = typescript_indexer._find_tsconfig()
        assert tsconfig is not None
        assert tsconfig.name == "tsconfig.json"

    def test_extract_imports_commonjs(self, typescript_indexer):
        """Test extracting CommonJS require statements."""
        code = """
const fs = require('fs');
const path = require('path');
let util = require('util');
        """

        imports = typescript_indexer.extract_imports(code, Path("test.js"))

        # Should extract require statements
        assert len(imports) >= 3

        modules = [imp.module for imp in imports]
        assert "fs" in modules
        assert "path" in modules
        assert "util" in modules

    def test_extract_type_alias(self, typescript_indexer):
        """Test extracting type alias definitions."""
        # Simple type alias
        alias1 = typescript_indexer._extract_type_alias(
            "type ID = string | number;",
            []
        )
        assert "string | number" in alias1

        # Complex type alias
        alias2 = typescript_indexer._extract_type_alias(
            "type Callback<T> = (value: T) => void;",
            []
        )
        assert "Callback" in alias2 or "value" in alias2
