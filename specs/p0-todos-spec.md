# P0-1: Complete TODO Items - Specification

**Priority**: P0 (Critical)
**Effort**: 1 day
**Impact**: HIGH (removes technical debt, unlocks features)

## TODO Items to Address

### 1. JSON Schema → GBNF Grammar Conversion
**Location**: `src/maze/orchestrator/providers/__init__.py:405`
**Context**: OpenAI provider uses JSON Schema, but llguidance uses GBNF

**Current Code**:
```python
# TODO: Convert JSON Schema to GBNF grammar
```

**Task**: Implement schema → grammar conversion for provider compatibility

**Subtasks**:
- Research GBNF format requirements
- Create schema_to_gbnf() function
- Handle common schema patterns (object, array, string, number)
- Add tests (5 tests)

**Exit Criteria**:
- JSON Schema converts to valid GBNF
- OpenAI provider can use grammar constraints
- Tests cover common schemas

---

### 2. Schema-Specific Constraints
**Location**: `src/maze/integrations/llguidance/adapter.py:304`

**Current Code**:
```python
# TODO: Add schema-specific constraints
```

**Task**: Add JSON Schema validation to llguidance integration

**Subtasks**:
- Implement schema validation in adapter
- Support %json directive in grammars
- Test with JSON output requirements
- Add tests (5 tests)

**Exit Criteria**:
- JSON Schema constraints enforced
- %json directive works in grammars
- Validated with JSON generation test

---

### 3. Pattern Mining for Python
**Location**: `src/maze/learning/pattern_mining.py:483`

**Current Code**:
```python
return []  # TODO: Add support for other languages
```

**Task**: Extend pattern mining to support Python

**Subtasks**:
- Add Python AST traversal for patterns
- Extract Python idioms (list comprehensions, context managers)
- Detect common patterns (error handling, decorators)
- Add tests (5 tests)

**Exit Criteria**:
- Python patterns extracted successfully
- Pattern quality matches TypeScript
- Tests validate Python-specific idioms

---

### 4. Mnemosyne Agent Orchestration
**Location**: `src/maze/integrations/mnemosyne/__init__.py:568`

**Current Code**:
```python
# TODO: Implement full orchestration with mnemosyne agents
```

**Task**: Complete mnemosyne multi-agent orchestration

**Subtasks**:
- Research mnemosyne agent API
- Implement agent coordination
- Add distributed pattern recall
- Add tests (5 tests)

**Exit Criteria**:
- Multi-agent pattern recall works
- Improved recall accuracy
- Tests validate orchestration

---

## Implementation Order

1. **Pattern Mining for Python** (2 hours) - Highest immediate value
2. **Schema Constraints** (3 hours) - Enables JSON generation
3. **JSON Schema → GBNF** (3 hours) - Provider compatibility
4. **Mnemosyne Orchestration** (4 hours) - Nice to have

**Total**: ~12 hours (1.5 days)

## Test Plan

**New Tests**: 20
- Pattern mining: 5 tests
- Schema constraints: 5 tests
- Schema → GBNF: 5 tests
- Mnemosyne orchestration: 5 tests

**Total After P0**: 1063 + 20 = **1083 tests**

## Dependencies

- Pattern mining: Requires PythonIndexer ✅
- Schema features: Requires llguidance ✅
- Mnemosyne: Requires MnemosyneIntegration ✅

## Risk Assessment

**Low Risk**: All items are localized changes with clear requirements
