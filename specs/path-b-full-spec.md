# Path B: Python Language Support - Full Specification

**Status**: 📋 Detailed Planning (Phase 2: Spec → Full Spec)
**Dependencies**: Path A complete ✅

## Component Breakdown

### 1. Python Indexer (maze-pb.1)

**Purpose**: Extract symbols, types, and patterns from Python codebases

**Interface** (Typed Hole):
```python
class PythonIndexer(BaseIndexer):
    def __init__(self, project_path: Optional[Path] = None): ...
    
    def index_file(self, file_path: Path) -> IndexingResult: ...
    def index_directory(self, directory: Path) -> IndexingResult: ...
    
    def _extract_symbols_from_ast(self, tree: ast.Module) -> List[Symbol]: ...
    def _extract_type_hints(self, node: ast.AST) -> str: ...
    def _detect_test_patterns(self, tree: ast.Module) -> List[TestCase]: ...
    def _detect_style(self, content: str) -> StyleInfo: ...
```

**Symbols to Extract**:
- Functions (regular and async)
- Classes (including dataclasses, Pydantic models)
- Methods (instance, class, static)
- Variables with type hints
- Type aliases (`TypeAlias`, `NewType`)
- Imports (standard and type-only)

**Type Hint Support** (PEP 484, 526, 604):
```python
def func(x: int) -> str: ...
async def fetch(url: str) -> dict[str, Any]: ...
x: list[int] = []
User: TypeAlias = dict[str, Any]
from typing import Optional, Union, List
```

**Test Pattern Detection**:
- pytest: `test_*`, `*_test.py`, `@pytest.fixture`
- unittest: `TestCase` classes, `test_*` methods
- doctest: `>>>` in docstrings

**Style Detection**:
- Indentation (spaces, typically 4)
- Quote preference (single vs double)
- Import style (sorting, grouping)
- Naming conventions (snake_case)

**Performance Target**: >1000 symbols/sec

**Test Coverage Target**: 85%
- AST parsing: 5 tests
- Symbol extraction: 5 tests
- Type hint parsing: 5 tests
- Test detection: 3 tests
- Style detection: 3 tests
- Integration: 4 tests
- **Total**: 25 tests

---

### 2. Python Grammar Templates (maze-pb.2)

**Purpose**: Lark grammar for Python syntax constraints

**Interface** (Typed Hole):
```python
# In src/maze/synthesis/grammars/python.py

PYTHON_FUNCTION = GrammarTemplate(
    name="python_function",
    language="python",
    grammar="""...Lark grammar..."""
)

PYTHON_CLASS = GrammarTemplate(...)
PYTHON_FILE = GrammarTemplate(...)
```

**Grammar Requirements**:
- Indentation handling (INDENT/DEDENT tokens)
- Function definitions (def, async def)
- Class definitions
- Type annotations
- Decorators
- Comprehensions
- Async/await
- Context managers
- Exception handling

**Indentation Strategy**:
- Use Python tokenizer to handle INDENT/DEDENT
- Lark grammar matches tokenized stream
- Preserve 4-space convention

**Performance Target**: <50ms compilation

**Test Coverage Target**: 70%
- Grammar validation: 5 tests
- Indentation handling: 3 tests
- Type annotation support: 4 tests
- Complex constructs: 3 tests
- **Total**: 15 tests

---

### 3. Python Validation Integration (maze-pb.3)

**Purpose**: Python-specific validation pipeline

**Components Needed**:

#### Syntax Validator
```python
class PythonSyntaxValidator:
    def validate(self, code: str) -> SyntaxValidationResult:
        # Use ast.parse to validate syntax
        ...
```

#### Type Validator
```python
class PythonTypeValidator:
    def validate(self, code: str) -> TypeValidationResult:
        # Use mypy or pyright
        ...
```

#### Lint Validator
```python
class PythonLintValidator:
    def validate(self, code: str) -> LintValidationResult:
        # Use ruff for linting
        ...
```

**Integration Points**:
- Update `Pipeline.index_project()` to select PythonIndexer
- Update `Pipeline._synthesize_constraints()` to load Python grammars
- Add Python validators to ValidationPipeline

**Test Coverage Target**: 75%
- Syntax validation: 3 tests
- Type validation: 3 tests
- Lint validation: 3 tests
- Pipeline integration: 3 tests
- **Total**: 12 tests

---

### 4. Python Examples (maze-pb.4)

**Purpose**: Working Python examples demonstrating capabilities

**Examples**:

1. **Function with Type Hints**
```python
# examples/python/01-function-generation.py
# Generate: def calculate_tax(price: float, rate: float) -> float: ...
```

2. **Dataclass Generation**
```python
# examples/python/02-dataclass.py
# Generate: @dataclass class User with fields and validation
```

3. **Async Function**
```python
# examples/python/03-async-function.py
# Generate: async def fetch_data(url: str) -> dict[str, Any]: ...
```

4. **FastAPI Endpoint**
```python
# examples/python/04-fastapi-endpoint.py
# Generate: @app.post("/users") async def create_user(user: UserCreate): ...
```

5. **Pytest Test Generation**
```python
# examples/python/05-test-generation.py
# Generate: comprehensive pytest tests for Calculator class
```

**Test Coverage**: 100% (all examples must run)
- 5 example execution tests
- 1 structure validation test
- **Total**: 6 tests

---

## Dependencies & Typed Holes

### New Files Required

1. **`src/maze/indexer/languages/python.py`** (450-500 lines)
   - Class: `PythonIndexer(BaseIndexer)`
   - Dependencies: `ast`, `typing` (stdlib)

2. **`src/maze/synthesis/grammars/python.py`** (300-400 lines)
   - Templates: `PYTHON_FUNCTION`, `PYTHON_CLASS`, `PYTHON_FILE`
   - Dependencies: `GrammarTemplate`

3. **`examples/python/*.py`** (5 files, ~500 lines total)
   - Runnable example scripts

4. **`tests/unit/test_indexer/test_python.py`** (~400 lines)
   - Tests for PythonIndexer

5. **`tests/unit/test_synthesis/test_python_grammar.py`** (~250 lines)
   - Tests for Python grammar templates

6. **`tests/unit/test_examples/test_python_examples.py`** (~100 lines)
   - Tests for Python examples

### Modified Files

1. **`src/maze/core/pipeline.py`**
   - Add Python indexer selection
   - Add Python grammar loading

2. **`src/maze/synthesis/grammars/__init__.py`**
   - Export Python templates

---

## Test Plan

### Unit Tests (52 total)
- PythonIndexer: 25 tests
- Python grammar: 15 tests
- Python validation: 12 tests

### Example Tests (6 total)
- Python examples: 6 tests

**Total New Tests**: 58
**Combined Total**: 1039 + 58 = **1097 tests** 🎯

---

## Implementation Order (Critical Path)

```
Day 1: PythonIndexer (8h)
    ↓
Day 2: Python Grammar (parallel, can start immediately)
    ↓
Day 3: Validation Integration (requires both)
    ↓
Day 4: Examples (requires Day 3)
    ↓
Day 5: Documentation (requires Day 4)
```

**Total**: 21-29 hours (~3-4 days)

---

## Constraints & Edge Cases

### Type Hint Edge Cases
```python
# Union types (PEP 604)
def func(x: int | str) -> bool: ...

# Optional (two forms)
def func(x: Optional[int]) -> None: ...
def func(x: int | None) -> None: ...

# Generic types
def func(items: list[T]) -> T: ...

# TypeVar
T = TypeVar('T', bound=BaseModel)

# Protocol
class Comparable(Protocol): ...

# Literal
def func(mode: Literal['r', 'w']) -> None: ...
```

### Indentation Complexity
```python
# Nested indentation
class Outer:
    class Inner:
        def method(self):
            if True:
                return 1
```

### Decorator Handling
```python
@dataclass
@cache
def func(): ...
```

### Async Support
```python
async def fetch(): ...
async with lock: ...
async for item in stream: ...
```

---

## Performance Targets

| Operation | Target | Validation Method |
|-----------|--------|-------------------|
| Symbol extraction | >1000 symbols/sec | Benchmark |
| File indexing | <100ms per 1K LOC | Benchmark |
| Grammar compilation | <50ms | Unit test |
| Type hint parsing | <1ms per hint | Unit test |

---

## Success Criteria

1. ✅ `maze init --language python` creates Python project
2. ✅ `maze index` extracts Python symbols and types
3. ✅ `maze generate "Create Python function"` produces valid code
4. ✅ Type hints correctly parsed and used in constraints
5. ✅ Grammar handles indentation correctly
6. ✅ All 5 Python examples run successfully
7. ✅ Test coverage: 80%+ for new components
8. ✅ Performance: matches TypeScript indexer speed

---

## Next Steps

After full spec approval:
1. Implement PythonIndexer with AST parsing
2. Create Python grammar templates
3. Integrate validation
4. Create examples
5. Document
