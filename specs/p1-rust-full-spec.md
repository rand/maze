# P1: Rust Language Support - Full Specification

**Status**: 📋 Detailed Planning (Phase 2: Spec → Full Spec)
**Dependencies**: P0 complete ✅, Python pattern established ✅

## Component Breakdown

### 1. Rust Indexer (p1-rust.1)

**Purpose**: Extract symbols, types, and patterns from Rust codebases

**Interface** (Typed Hole):
```python
class RustIndexer(BaseIndexer):
    def __init__(self, project_path: Optional[Path] = None, use_analyzer: bool = True): ...
    
    def index_file(self, file_path: Path) -> IndexingResult: ...
    def index_directory(self, directory: Path) -> IndexingResult: ...
    
    def _extract_with_rust_analyzer(self, path: Path) -> Dict[str, Any]: ...
    def _extract_with_tree_sitter(self, code: str, file_path: str) -> List[Symbol]: ...
    def _parse_lifetime(self, lifetime_str: str) -> str: ...
    def _parse_trait_bounds(self, bounds_str: str) -> List[str]: ...
```

**Symbols to Extract**:

#### Functions
```rust
fn process(data: &str) -> Result<String, Error>
pub fn new() -> Self
pub async fn fetch<T: Serialize>(url: &str) -> Result<T, Error>
```

#### Structs with Lifetimes
```rust
pub struct User<'a> {
    name: &'a str,
    email: String,
}

struct Ref<'a, T: Clone> {
    data: &'a T,
}
```

#### Traits
```rust
pub trait Repository<T> {
    fn find(&self, id: &str) -> Option<T>;
    fn save(&mut self, item: T) -> Result<(), Error>;
}
```

#### Impl Blocks
```rust
impl<T> Repository<T> for InMemoryRepo<T> {
    fn find(&self, id: &str) -> Option<T> { }
}

impl User {
    pub fn new(name: String) -> Self { }
}
```

#### Enums and Type Aliases
```rust
pub enum Result<T, E> {
    Ok(T),
    Err(E),
}

type UserId = u64;
struct Email(String);  // Newtype
```

**Integration Strategy**:

**Option A: rust-analyzer LSP** (Recommended)
- More accurate type information
- Handles lifetimes correctly
- Gets trait bounds
- Slower but comprehensive

**Option B: tree-sitter-rust**
- Faster parsing
- AST-based extraction
- May miss complex type info
- Good for syntax-level patterns

**Hybrid Approach**: tree-sitter for basic, rust-analyzer for types

**Test Coverage Target**: 85%
- Basic extraction: 8 tests
- Lifetime parsing: 4 tests
- Trait extraction: 3 tests
- Impl blocks: 3 tests
- Integration: 2 tests
- **Total**: 20 tests

---

### 2. Rust Grammar Validation (p1-rust.2)

**Purpose**: Validate and enhance existing Rust grammar templates

**Existing Templates**: `src/maze/synthesis/grammars/rust.py`
- RUST_FUNCTION
- RUST_STRUCT  
- RUST_IMPL

**Need to Validate**:
- Lifetime syntax: `'a`, `'static`, `'b`
- Generic bounds: `<T: Clone + Send>`
- Trait syntax: `trait Name { }`
- Result types: `Result<T, E>`
- Ownership: `&`, `&mut`, move semantics
- Async: `async fn`, `.await`

**Test Coverage Target**: 70%
- Lifetime syntax: 3 tests
- Generic bounds: 3 tests
- Trait definitions: 2 tests
- Result types: 2 tests
- **Total**: 10 tests

---

### 3. Rust Validation Integration (p1-rust.3)

**Purpose**: Rust-specific validation using cargo tooling

**Components**:

#### Syntax Validator
```python
class RustSyntaxValidator:
    def validate(self, code: str) -> SyntaxValidationResult:
        # Use cargo check or rustc --parse
        ...
```

#### Type Validator
```python
class RustTypeValidator:
    def validate(self, code: str, project_path: Path) -> TypeValidationResult:
        # Use cargo check with JSON output
        ...
```

#### Lint Validator
```python
class RustLintValidator:
    def validate(self, code: str) -> LintValidationResult:
        # Use cargo clippy
        ...
```

**Integration**:
- Update Pipeline to select RustIndexer for "rust" language
- Add Rust grammar loading in _synthesize_constraints
- Add Rust validators (optional, graceful if cargo missing)

**Test Coverage**: 75%
- Syntax validation: 2 tests
- Type validation: 2 tests
- Pipeline integration: 1 test
- **Total**: 5 tests

---

### 4. Rust Examples (p1-rust.4)

**Examples**:

1. **Function with Result**
```python
# examples/rust/01-function-result.py
# Generate: fn divide(a: f64, b: f64) -> Result<f64, String>
```

2. **Struct with Trait Implementation**
```python
# examples/rust/02-struct-trait.py
# Generate: struct User + impl Display for User
```

3. **Async Function with Tokio**
```python
# examples/rust/03-async-tokio.py
# Generate: async fn fetch_data(url: &str) -> Result<String, Error>
```

4. **Error Handling**
```python
# examples/rust/04-error-handling.py
# Generate: Custom error type with thiserror
```

5. **Test Generation**
```python
# examples/rust/05-test-generation.py
# Generate: #[test] functions and #[cfg(test)] module
```

**Test Coverage**: 100%
- 5 example execution tests
- 1 structure validation test
- **Total**: 6 tests

---

## Dependencies & Typed Holes

### New Files Required

1. **`src/maze/indexer/languages/rust.py`** (500-600 lines)
   - Class: `RustIndexer(BaseIndexer)`
   - Dependencies: `tree-sitter-rust` ✅, optional `rust-analyzer`

2. **`examples/rust/*.py`** (5 files, ~500 lines)

3. **`tests/unit/test_indexer/test_rust.py`** (~400 lines, 20 tests)

4. **`tests/unit/test_synthesis/test_rust_grammar.py`** (~200 lines, 10 tests)

5. **`tests/unit/test_examples/test_rust_examples.py`** (~100 lines, 6 tests)

6. **`docs/user-guide/rust-guide.md`** (~400 lines)

### Modified Files

1. **`src/maze/core/pipeline.py`**
   - Add Rust indexer selection
   - Add Rust grammar loading

2. **`src/maze/synthesis/grammars/__init__.py`**
   - Export Rust templates

---

## Test Plan

**New Tests**: 41
- RustIndexer: 20 tests
- Rust grammar: 10 tests
- Validation integration: 5 tests
- Examples: 6 tests

**Total After P1-Rust**: 1079 + 41 = **1120 tests**

---

## Implementation Order

```
Day 1: RustIndexer (8h)
    ↓
Day 2: Grammar Validation (4h) [can be parallel]
    ↓
Day 3: Validation Integration (4h)
    ↓
Day 4: Examples + Docs (4h)
```

**Total**: 20 hours (~3 days)

---

## Rust-Specific Considerations

### Ownership and Borrowing
```rust
fn process(data: &str) -> String  // Borrow
fn consume(data: String) -> String  // Move
fn mutate(data: &mut Vec<i32>)  // Mutable borrow
```

### Lifetimes
```rust
struct Ref<'a> { data: &'a str }
fn longest<'a>(x: &'a str, y: &'a str) -> &'a str
```

### Trait Bounds
```rust
fn process<T: Clone + Send>(item: T) -> T
where T: Debug
```

### Result and Option
```rust
fn divide(a: f64, b: f64) -> Result<f64, String>
fn find(id: &str) -> Option<User>
```

### Async with Tokio
```rust
#[tokio::main]
async fn main() {
    let result = fetch().await;
}
```

---

## Success Criteria

1. ✅ `maze init --language rust` creates Rust project
2. ✅ `maze index` extracts Rust symbols with lifetimes
3. ✅ `maze generate "Create Rust function"` produces valid code
4. ✅ Lifetimes correctly parsed and displayed
5. ✅ Trait implementations extracted
6. ✅ All 5 Rust examples run
7. ✅ Performance matches Python/TypeScript
8. ✅ Cargo check validates generated code (if cargo available)

---

## Risk Mitigation

**Risk**: Lifetime complexity
**Mitigation**: Start with simple lifetimes, expand gradually

**Risk**: Trait system complexity
**Mitigation**: Focus on common patterns (Clone, Debug, Display)

**Risk**: cargo tooling required
**Mitigation**: Graceful degradation if cargo not installed

---

## Next Steps

After spec approval:
1. Create detailed implementation plan
2. Implement RustIndexer with tree-sitter
3. Validate grammar templates
4. Integrate with pipeline
5. Create examples
6. Test and document
