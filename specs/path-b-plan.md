# Path B: Python Language Support - Execution Plan

**Status**: 📋 Ready for Future Implementation (Phase 3: Full Spec → Plan)
**Timeline**: 3-5 days
**Critical Path**: Python Indexer → Grammar Templates → Validation → Examples

## Task Ordering & Dependencies

### Day 1: Python Indexer Core (maze-pb.1)
**Duration**: 6-8 hours

**Subtasks**:
1. Create `src/maze/indexer/languages/python.py`
2. Implement `PythonIndexer(BaseIndexer)`
3. AST parsing with `ast` module
4. Symbol extraction (functions, classes, variables)
5. Type hint parsing (PEP 484, 526)
6. Import tracking
7. Unit tests (15 tests)

**Dependencies**: None
**Output**: PythonIndexer extracts symbols from .py files

**Exit Criteria**:
- Extracts functions with type hints
- Extracts classes and methods
- Parses type annotations correctly
- Performance: >1000 symbols/sec
- 15 tests passing

---

### Day 2: Python Grammar & Style Detection (maze-pb.2)
**Duration**: 6-8 hours

**Subtasks**:
1. Create `src/maze/synthesis/grammars/python.lark`
2. Python syntax rules (functions, classes, statements)
3. Indentation handling (critical for Python)
4. Type annotation support
5. Style detection (PEP 8, Black compatibility)
6. Grammar tests (10 tests)

**Dependencies**: None (parallel with Day 1)
**Output**: Python grammar template

**Exit Criteria**:
- Grammar validates Python syntax
- Handles indentation correctly
- Supports type annotations
- Compilation: <50ms
- 10 tests passing

---

### Day 3: Validation & Integration (maze-pb.3)
**Duration**: 4-6 hours

**Subtasks**:
1. Python syntax validator integration
2. Type checking (mypy integration)
3. Linting (ruff integration)
4. Test pattern detection (pytest, unittest)
5. Update pipeline to support "python" language
6. Integration tests (8 tests)

**Dependencies**: Indexer (maze-pb.1), Grammar (maze-pb.2)
**Output**: Full Python validation pipeline

**Exit Criteria**:
- `maze init --language python` works
- `maze index` works on Python projects
- Validation catches Python errors
- 8 tests passing

---

### Day 4: Python Examples (maze-pb.4)
**Duration**: 3-4 hours

**Subtasks**:
1. Function generation example
2. Class with dataclass example
3. Async function example
4. FastAPI endpoint example
5. Test generation example (pytest)
6. Example tests (5 tests)

**Dependencies**: Validation (maze-pb.3)
**Output**: 5 working Python examples

**Exit Criteria**:
- All examples run without errors
- Generated code is valid Python
- Types check correctly
- 5 example tests passing

---

### Day 5: Documentation & Polish (maze-pb.5)
**Duration**: 2-3 hours

**Subtasks**:
1. Python getting started guide
2. Python-specific best practices
3. Update API reference
4. Update CLAUDE.md indexer section
5. README updates

**Dependencies**: Examples (maze-pb.4)
**Output**: Complete Python documentation

---

## Critical Path

```
Day 1: Python Indexer (6-8h)
         ↓
Day 3: Validation Integration (4-6h)
         ↓
Day 4: Examples (3-4h)
         ↓
Day 5: Documentation (2-3h)

Parallel:
Day 2: Grammar Templates (6-8h) → merges into Day 3
```

**Total**: 21-29 hours (~3-4 days)

## Test Plan

**New Tests**: ~38
- PythonIndexer: 15 tests
- Python grammar: 10 tests
- Validation integration: 8 tests
- Python examples: 5 tests

**Total After Path B**: 1040 + 38 = **1078 tests**

## Language-Specific Considerations

### Type Hints
```python
# Must parse:
def func(x: int) -> str: ...
async def fetch(url: str) -> dict[str, Any]: ...
class User(BaseModel): ...
x: list[int] = []
```

### Indentation
- Critical for Python grammar
- Lark grammar must handle INDENT/DEDENT tokens
- Use Python tokenizer for accuracy

### Testing Frameworks
- pytest (primary - most popular)
- unittest (secondary)
- doctest (optional)

### Style
- PEP 8 compliance
- Black formatter compatibility
- Import sorting (isort)

## Integration Points

- `Pipeline.index_project()` - Add Python indexer selection
- `GrammarBuilder` - Load python.lark template
- `ValidationPipeline` - Add Python validators
- CLI - Already supports `--language python`

## Performance Targets

Same as TypeScript:
- Indexing: <30s for 100K LOC
- Symbol extraction: >1000 symbols/sec
- Grammar compilation: <50ms
- Validation: <500ms

## Risk Assessment

**Medium Risk**:
- Indentation grammar complexity
- Type hint variation (many PEPs)
- Multiple testing frameworks

**Mitigation**:
- Use Python tokenizer for indentation
- Start with common type patterns
- Focus on pytest initially
