# Path B: Python Language Support - Specification

**Status**: 📋 Planning (Phase 1: Prompt → Spec)
**Priority**: MEDIUM - Expands language support
**Estimated Duration**: 3-5 days
**Dependencies**: Path A recommended (for testing actual generation)

## Executive Summary

Path B adds full Python language support to Maze, including indexing, grammar templates, validation, and examples. Python is the second most requested language after TypeScript and critical for ML/data science use cases.

## Problem Statement

Current limitations:
1. Only TypeScript indexer implemented
2. No Python grammar templates
3. No Python-specific validation
4. No Python examples

**Impact**: Cannot generate Python code, limiting audience to TypeScript users.

## Objectives

### 1. Python Indexer
**Goal**: Extract symbols, types, patterns from Python codebases

**Components Needed**:
- `PythonIndexer` class extending `BaseIndexer`
- AST parsing with Python `ast` module
- Type hint extraction (PEP 484, 526)
- Function/class/method extraction
- Import tracking
- Test pattern detection (pytest, unittest)
- Style detection (PEP 8)

**Performance Target**: 1000 symbols/sec (same as TypeScript)

### 2. Python Grammar Templates
**Goal**: Lark grammar for Python syntax constraints

**Components Needed**:
- `python.lark` grammar file
- Support for Python 3.11+ syntax
- Indentation handling
- Type annotation support
- Async/await patterns
- Comprehensions and generators

**Performance Target**: <50ms compilation

### 3. Python Validation
**Goal**: Python-specific validation pipeline

**Components Needed**:
- Syntax validation with `ast.parse`
- Type checking with mypy or pyright
- Linting with ruff
- Test execution integration

### 4. Python Examples
**Goal**: Working Python examples

**Examples Needed**:
- Function generation with type hints
- Class with dataclass
- Async function with error handling
- FastAPI endpoint
- Test generation with pytest

## Scope

### In Scope
- Python indexer with AST parsing
- Python grammar template
- Type hint extraction (PEP 484)
- Basic validation (syntax, types)
- 5 Python examples
- Tests for all components

### Out of Scope
- Advanced type features (Protocol, TypeVar bounds)
- Multiple Python versions (<3.11)
- Python 2 compatibility
- Jupyter notebook support

## Dependencies

### External Libraries
- `ast` module (stdlib) - AST parsing
- `tree-sitter-python` (already installed) - Alternative parser
- `mypy` or `pyright` (already installed) - Type checking
- `ruff` (already installed) - Linting

### Internal Components
- `BaseIndexer` ✅
- `GrammarBuilder` ✅
- `ValidationPipeline` ✅
- `Pipeline` ✅

## Success Criteria

1. ✅ `PythonIndexer` extracts symbols from Python files
2. ✅ Grammar template validates Python syntax
3. ✅ Type hints correctly extracted and used
4. ✅ `maze init --language python` works
5. ✅ `maze generate "Create Python function"` produces valid code
6. ✅ Python examples run successfully
7. ✅ Test coverage: 80%+ for new components

## Estimated Breakdown

- PythonIndexer: 1.5 days (15 tests)
- Python grammar: 1 day (10 tests)
- Validation integration: 0.5 days (5 tests)
- Examples: 0.5 days (5 examples)
- Documentation: 0.5 days
- **Total**: 4 days

## Risk Assessment

**Medium Risk**:
- Python indentation in grammar (complex)
- Type hint parsing (many PEP variations)
- Multiple testing frameworks (pytest, unittest, etc.)

**Mitigation**:
- Use tree-sitter-python for robust parsing
- Start with common type hint patterns
- Support pytest first (most popular)

## Next Steps

After spec approval:
1. Create full-spec.md with typed holes
2. Create plan.md with task ordering
3. Implement PythonIndexer first
4. Add grammar template
5. Create examples
6. Test end-to-end
