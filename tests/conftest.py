"""
Pytest configuration and fixtures for Maze test suite.
"""

# Add src directory to path for imports
import sys
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from maze.core.constraints import ConstraintSet, SyntacticConstraint, TypeConstraint
from maze.core.types import FunctionSignature, Type, TypeContext, TypeParameter
from maze.indexer.languages.typescript import TypeScriptIndexer
from maze.integrations.llguidance import LLGuidanceAdapter, TokenizerConfig

# Fixtures for core types


@pytest.fixture
def simple_type() -> Type:
    """Create a simple type for testing."""
    return Type("string")


@pytest.fixture
def generic_type() -> Type:
    """Create a generic type for testing."""
    return Type("Array", (Type("number"),))


@pytest.fixture
def type_context() -> TypeContext:
    """Create a TypeContext with sample data."""
    context = TypeContext(language="typescript")
    context.variables["userName"] = Type("string")
    context.variables["userAge"] = Type("number")
    context.functions["greet"] = FunctionSignature(
        name="greet", parameters=[TypeParameter("name", Type("string"))], return_type=Type("string")
    )
    return context


# Fixtures for constraints


@pytest.fixture
def syntactic_constraint() -> SyntacticConstraint:
    """Create a syntactic constraint for testing."""
    grammar = """
        ?start: statement+
        statement: assignment | function_def
        assignment: IDENT "=" expression ";"
        function_def: "function" IDENT "(" ")" block
        IDENT: /[a-zA-Z_][a-zA-Z0-9_]*/
        %ignore /\\s+/
    """
    return SyntacticConstraint(grammar=grammar, language="typescript")


@pytest.fixture
def type_constraint(type_context: TypeContext) -> TypeConstraint:
    """Create a type constraint for testing."""
    return TypeConstraint(expected_type=Type("string"), context=type_context, strict=True)


@pytest.fixture
def constraint_set(
    syntactic_constraint: SyntacticConstraint, type_constraint: TypeConstraint
) -> ConstraintSet:
    """Create a constraint set for testing."""
    constraints = ConstraintSet()
    constraints.add(syntactic_constraint)
    constraints.add(type_constraint)
    return constraints


# Fixtures for llguidance


@pytest.fixture
def llguidance_adapter() -> LLGuidanceAdapter:
    """Create an LLGuidanceAdapter for testing."""
    return LLGuidanceAdapter(
        tokenizer_config=TokenizerConfig(vocab_size=10000),
        mask_cache_size=1000,
        enable_profiling=True,
    )


# Fixtures for indexing


@pytest.fixture
def temp_project(tmp_path: Path) -> Path:
    """Create a temporary project structure for testing."""
    # Create project structure
    src_dir = tmp_path / "src"
    src_dir.mkdir()

    # Create sample TypeScript file
    ts_file = src_dir / "example.ts"
    ts_file.write_text(
        """
export interface User {
    name: string;
    age: number;
}

export function greetUser(user: User): string {
    return `Hello, ${user.name}!`;
}

export const defaultUser: User = {
    name: "Alice",
    age: 30
};

// Test function
describe("greetUser", () => {
    it("should greet the user by name", () => {
        const user: User = { name: "Bob", age: 25 };
        expect(greetUser(user)).toBe("Hello, Bob!");
    });
});
"""
    )

    # Create package.json
    package_json = tmp_path / "package.json"
    package_json.write_text(
        """{
    "name": "test-project",
    "version": "1.0.0",
    "scripts": {
        "test": "jest"
    }
}"""
    )

    # Create tsconfig.json
    tsconfig = tmp_path / "tsconfig.json"
    tsconfig.write_text(
        """{
    "compilerOptions": {
        "target": "ES2020",
        "module": "commonjs",
        "strict": true
    }
}"""
    )

    return tmp_path


@pytest.fixture
def typescript_indexer(temp_project: Path) -> TypeScriptIndexer:
    """Create a TypeScript indexer with a temp project."""
    return TypeScriptIndexer(project_path=temp_project)


# Fixtures for sample code


@pytest.fixture
def sample_typescript_code() -> str:
    """Sample TypeScript code for testing."""
    return """
interface Person {
    name: string;
    age: number;
}

function greet(person: Person): string {
    return `Hello, ${person.name}!`;
}

const alice: Person = {
    name: "Alice",
    age: 30
};

console.log(greet(alice));
"""


@pytest.fixture
def sample_python_code() -> str:
    """Sample Python code for testing."""
    return """
from typing import Dict, List

def process_items(items: List[Dict[str, any]]) -> Dict[str, int]:
    \"\"\"Process a list of items and return statistics.\"\"\"
    stats = {"total": len(items)}

    for item in items:
        category = item.get("category", "unknown")
        stats[category] = stats.get(category, 0) + 1

    return stats

# Test the function
test_items = [
    {"name": "A", "category": "foo"},
    {"name": "B", "category": "bar"},
    {"name": "C", "category": "foo"},
]

result = process_items(test_items)
print(result)
"""


# Performance testing fixtures


@pytest.fixture
def performance_benchmark() -> dict[str, Any]:
    """Configuration for performance benchmarks."""
    return {
        "mask_computation_target_us": 100,  # Target: <100μs
        "grammar_compilation_target_ms": 50,  # Target: <50ms
        "type_search_target_ms": 1,  # Target: <1ms
        "iterations": 1000,  # Number of iterations for benchmarking
    }


# Cleanup fixture


@pytest.fixture(autouse=True)
def cleanup_after_test():
    """Clean up after each test."""
    yield
    # Any cleanup code here


# Pytest configuration


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "unit: marks tests as unit tests")
    config.addinivalue_line("markers", "performance: marks tests as performance benchmarks")
