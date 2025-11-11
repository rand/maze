# P1: Rust Language Support - Specification

**Priority**: P1 (High Impact)
**Effort**: 3-4 days
**Impact**: HIGH (systems programming, #3 requested language)
**Dependencies**: Path B complete ✅ (Python pattern established)

## Executive Summary

Add full Rust language support to Maze, following the proven pattern from TypeScript and Python. Rust is critical for systems programming, embedded systems, and performance-critical applications.

## Problem Statement

**Current State**:
- TypeScript ✅ (indexer, grammar, examples)
- Python ✅ (indexer, grammar, examples)
- Rust ❌ (grammar templates exist but no indexer)

**Gap**: Cannot generate Rust code, missing ~30% of target audience

## Objectives

### 1. Rust Indexer with rust-analyzer Integration
**Goal**: Extract symbols, types, and patterns from Rust codebases

**Rust-Specific Challenges**:
- Lifetime annotations (`'a`, `'static`, `'b`)
- Trait bounds (`T: Clone + Send`)
- Impl blocks (separate from struct definitions)
- Macro invocations
- Visibility modifiers (pub, pub(crate), pub(super))
- Associated types and constants

**Symbols to Extract**:
```rust
// Functions
fn process(data: &str) -> Result<String, Error> { }
pub async fn fetch<T>(url: &str) -> Result<T, Error> { }

// Structs with lifetimes
struct Ref<'a, T> {
    data: &'a T,
}

// Traits
pub trait Processor<T> {
    fn process(&self, input: T) -> Result<T, Error>;
}

// Impl blocks
impl<T> Processor<T> for MyProcessor {
    fn process(&self, input: T) -> Result<T, Error> { }
}

// Enums
enum Result<T, E> {
    Ok(T),
    Err(E),
}

// Type aliases
type UserId = u64;
struct Email(String);  // Newtype pattern
```

### 2. Rust Grammar Templates
**Goal**: Lark grammar for Rust syntax constraints

**Already Exists**: `src/maze/synthesis/grammars/rust.py`

**Needs Validation**:
- Lifetime syntax handling
- Generic bounds syntax
- Trait syntax
- Macro syntax (basic support)
- Visibility modifiers

### 3. Rust Validation
**Goal**: Rust-specific validation pipeline

**Tools**:
- `cargo check` - Basic syntax and type checking
- `clippy` - Linting
- `cargo test` - Test execution

### 4. Rust Examples
**Goal**: 5 working examples

1. Function with Result and lifetimes
2. Struct with trait implementation
3. Async function with tokio
4. Error handling with Result
5. Test generation with #[test]

## Scope

### In Scope
- RustIndexer with rust-analyzer or cargo metadata
- Validate existing Rust grammar templates
- Integration with cargo tooling
- 5 Rust examples
- ~40 tests

### Out of Scope
- Procedural macros (complex)
- Unsafe code generation
- Advanced lifetime inference
- Cross-compilation support

## Dependencies

### External Tools
- `rust-analyzer` (LSP) or `cargo metadata` (JSON output)
- `cargo` (build tool)
- `clippy` (linter)
- Already have: `tree-sitter-rust` ✅

### Internal Components
- BaseIndexer ✅
- GrammarBuilder ✅
- Grammar templates (exist, need validation) ✅
- Pipeline ✅

## Success Criteria

1. ✅ `maze init --language rust` works
2. ✅ RustIndexer extracts structs, enums, functions, traits, impls
3. ✅ Lifetime annotations parsed correctly
4. ✅ Grammar handles Rust syntax
5. ✅ `maze generate "Create Rust function"` produces valid code
6. ✅ All 5 examples run successfully
7. ✅ Test coverage: 80%+
8. ✅ Performance: matches TypeScript/Python

## Performance Targets

- Indexing: <30s for 100K LOC
- Symbol extraction: >800 symbols/sec (Rust is more complex)
- Grammar compilation: <50ms

## Risk Assessment

**Medium Risk**:
- Lifetimes add complexity
- Trait system is sophisticated
- Multiple valid patterns (Result vs panic, RefCell vs Arc)

**Mitigation**:
- Start with common patterns
- Use rust-analyzer for accurate parsing
- Support most common lifetime patterns first

## Estimated Breakdown

- Day 1: RustIndexer (8h, 20 tests)
- Day 2: Grammar validation and updates (4h, 10 tests)
- Day 3: Validation integration (4h, 5 tests)
- Day 4: Examples and docs (4h, 5 tests)
- **Total**: 20 hours (~3 days)

## Next Steps

1. Create full spec with typed holes
2. Create implementation plan
3. Implement RustIndexer
4. Validate grammar templates
5. Create examples
6. Test end-to-end
