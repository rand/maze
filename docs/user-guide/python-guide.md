# Python Language Guide

Complete guide for using Maze with Python projects.

## Quick Start

```bash
# Initialize Python project
maze init --language python

# Create Python file
echo "def hello(): pass" > main.py

# Index project
maze index .

# Generate code
maze generate "Create a function to validate email addresses"
```

## Type Hints Support

Maze fully supports Python type hints (PEP 484, 526, 604):

### Basic Types

```python
def greet(name: str) -> str:
    return f"Hello, {name}!"

age: int = 25
scores: list[float] = [95.5, 87.0]
```

### Union Types (PEP 604)

```python
def process(value: int | str) -> bool:
    return True

# Alternative syntax (older)
from typing import Union
def process(value: Union[int, str]) -> bool:
    return True
```

### Optional Types

```python
def find_user(id: str) -> dict[str, Any] | None:
    return None

# Alternative
from typing import Optional
def find_user(id: str) -> Optional[dict]:
    return None
```

### Generic Types

```python
from typing import TypeVar, Generic

T = TypeVar('T')

def first(items: list[T]) -> T | None:
    return items[0] if items else None

class Repository(Generic[T]):
    def save(self, item: T) -> None:
        pass
```

## Dataclasses

Maze understands dataclass patterns:

```python
from dataclasses import dataclass

@dataclass
class User:
    id: str
    name: str
    email: str
    age: int | None = None
    
    def __post_init__(self):
        if not self.email:
            raise ValueError("Email required")
```

## Async/Await

Full support for async Python:

```python
async def fetch_data(url: str) -> dict[str, Any]:
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.json()

async for item in async_generator():
    process(item)
```

## Testing Support

Maze recognizes pytest and unittest patterns:

### Pytest

```python
def test_addition():
    assert 1 + 1 == 2

@pytest.fixture
def sample_data():
    return {"key": "value"}

def test_with_fixture(sample_data):
    assert sample_data["key"] == "value"
```

### Unittest

```python
import unittest

class TestMath(unittest.TestCase):
    def test_addition(self):
        self.assertEqual(1 + 1, 2)
    
    def setUp(self):
        self.data = []
```

## FastAPI Integration

Generate type-safe FastAPI endpoints:

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class CreateUser(BaseModel):
    name: str
    email: str

class UserResponse(BaseModel):
    id: str
    name: str
    email: str

@app.post("/users", response_model=UserResponse)
async def create_user(user: CreateUser) -> UserResponse:
    # Implementation
    return UserResponse(id="123", name=user.name, email=user.email)
```

## Style Conventions

Maze learns and follows PEP 8:

### Naming Conventions

- Functions: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Private: `_leading_underscore`

### Formatting

- Indentation: 4 spaces
- Line length: 79-100 characters
- Quotes: Determined from codebase (single or double)
- Imports: Grouped (stdlib, third-party, local)

## Common Patterns

### Error Handling

```python
def divide(a: float, b: float) -> float:
    if b == 0:
        raise ValueError("Division by zero")
    return a / b

try:
    result = divide(10, 0)
except ValueError as e:
    print(f"Error: {e}")
```

### Context Managers

```python
def read_file(path: str) -> str:
    with open(path, 'r') as f:
        return f.read()
```

### Comprehensions

```python
squares = [x**2 for x in range(10)]
evens = {x for x in range(10) if x % 2 == 0}
lookup = {str(i): i for i in range(10)}
```

## Configuration

Python-specific configuration:

```toml
[project]
language = "python"
source_paths = ["src/", "lib/"]

[indexer]
excluded_dirs = [
    "__pycache__",
    ".venv",
    "venv",
    ".pytest_cache",
    ".mypy_cache",
]

[validation]
type_check = true  # Uses mypy
lint = true        # Uses ruff
```

## Type Checking

### With mypy

```bash
# Enable type checking
maze config set validation.type_check true

# Generate and validate
maze generate "Create typed function" | tee output.py
maze validate output.py --type-check
```

### With Pyright

Configure in `pyproject.toml`:

```toml
[tool.pyright]
typeCheckingMode = "strict"
```

## Linting

Maze integrates with ruff:

```bash
# Enable linting
maze config set validation.lint true

# Validate with lint
maze validate code.py
```

## Performance

Python indexing performance:

- **Small projects** (1K-5K LOC): ~5ms
- **Medium projects** (10K-50K LOC): ~50ms
- **Large projects** (100K+ LOC): ~500ms

Symbol extraction: >1000 symbols/sec ✅

## Best Practices

### Provide Type Hints in Prompts

```python
# Good
prompt = "Create function validate_email(email: str) -> bool"

# Better
prompt = """Create function:
def validate_email(email: str) -> bool:
    - Checks @ symbol present
    - Validates domain format
    - Returns True if valid"""
```

### Use Specific Framework Names

```python
# For FastAPI
prompt = "Create FastAPI POST endpoint with Pydantic models"

# For pytest
prompt = "Create pytest tests with fixtures"

# For dataclass
prompt = "Create dataclass with validation in __post_init__"
```

### Enable Type Constraints

```python
config.constraints.type_enabled = True

# Ensures generated code type-checks
# Prevents common type errors
# Guides generation toward type-correct expressions
```

## Common Issues

### Import Errors

Make sure required packages are importable:

```python
# If generating FastAPI code
pip install fastapi pydantic

# If generating async code
pip install httpx aiohttp
```

### Type Checking Failures

```bash
# Install type checkers
pip install mypy

# Check what failed
maze validate code.py --type-check
```

## Examples

See [examples/python/](../../examples/python/) for:

1. Function generation with type hints
2. Dataclass with validation
3. Async function with error handling
4. FastAPI endpoint generation
5. Pytest test generation

## Next Steps

- [Getting Started](getting-started.md) - General guide
- [Best Practices](best-practices.md) - Optimization tips
- [Provider Setup](provider-setup.md) - Configure LLM providers
- [Examples](../../examples/python/) - Working code examples
