# Rust Language Guide

Complete guide for using Maze with Rust projects.

## Quick Start

```bash
# Initialize Rust project
maze init --language rust

# Create Rust file
echo "fn main() {}" > src/main.rs

# Index project
maze index .

# Generate code
maze generate "Create a function that processes data with Result type"
```

## Rust-Specific Features

### Ownership and Borrowing

Maze understands Rust ownership patterns:

```rust
// Borrow
fn process(data: &str) -> String

// Mutable borrow
fn mutate(data: &mut Vec<i32>)

// Move semantics
fn consume(data: String) -> String
```

### Lifetimes

Full support for lifetime annotations:

```rust
// Simple lifetime
struct Ref<'a> {
    data: &'a str,
}

// Multiple lifetimes
fn longest<'a, 'b>(x: &'a str, y: &'b str) -> &'a str

// Static lifetime
const GLOBAL: &'static str = "value";
```

### Generic Types

Generic type parameters with bounds:

```rust
// Simple generic
fn first<T>(items: Vec<T>) -> Option<T>

// With trait bounds
fn process<T: Clone + Send>(item: T) -> T

// Where clauses
fn complex<T, U>(t: T, u: U) -> T
where
    T: Clone + Debug,
    U: Into<T>
```

### Traits

Trait definitions and implementations:

```rust
// Trait definition
pub trait Repository<T> {
    fn find(&self, id: &str) -> Option<T>;
    fn save(&mut self, item: T) -> Result<(), Error>;
}

// Impl for type
impl<T> Repository<T> for InMemoryRepo<T> {
    fn find(&self, id: &str) -> Option<T> {
        // Implementation
    }
}

// Derived traits
#[derive(Clone, Debug, PartialEq)]
struct User {
    name: String,
}
```

### Result and Option

Idiomatic error handling:

```rust
// Result for errors
fn divide(a: f64, b: f64) -> Result<f64, String> {
    if b == 0.0 {
        Err("Division by zero".to_string())
    } else {
        Ok(a / b)
    }
}

// Option for absence
fn find_user(id: &str) -> Option<User> {
    None
}

// ? operator for propagation
fn process() -> Result<(), Error> {
    let data = fetch()?;
    validate(data)?;
    Ok(())
}
```

### Async/Await with Tokio

Async Rust patterns:

```rust
#[tokio::main]
async fn main() {
    let result = fetch_data().await;
}

async fn fetch_data(url: &str) -> Result<String, reqwest::Error> {
    let response = reqwest::get(url).await?;
    response.text().await
}
```

### Pattern Matching

```rust
match result {
    Ok(value) => println!("Success: {}", value),
    Err(e) => eprintln!("Error: {}", e),
}

if let Some(user) = find_user("123") {
    println!("Found: {}", user.name);
}
```

## Common Patterns

### Error Types with thiserror

```rust
use thiserror::Error;

#[derive(Error, Debug)]
pub enum AppError {
    #[error("Not found: {0}")]
    NotFound(String),
    
    #[error("Invalid input: {0}")]
    Invalid(String),
    
    #[error("IO error")]
    Io(#[from] std::io::Error),
}
```

### Builder Pattern

```rust
pub struct Config {
    host: String,
    port: u16,
}

impl Config {
    pub fn builder() -> ConfigBuilder {
        ConfigBuilder::default()
    }
}

pub struct ConfigBuilder {
    host: Option<String>,
    port: Option<u16>,
}

impl ConfigBuilder {
    pub fn host(mut self, host: String) -> Self {
        self.host = Some(host);
        self
    }
    
    pub fn build(self) -> Result<Config, String> {
        // Validation and construction
    }
}
```

### Newtype Pattern

```rust
pub struct UserId(u64);
pub struct Email(String);

impl Email {
    pub fn new(s: String) -> Result<Self, String> {
        if s.contains('@') {
            Ok(Email(s))
        } else {
            Err("Invalid email".to_string())
        }
    }
}
```

## Testing

### Unit Tests

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_addition() {
        assert_eq!(add(2, 2), 4);
    }

    #[test]
    fn test_division() {
        assert!(divide(10.0, 0.0).is_err());
    }
}
```

### Integration Tests

```rust
// tests/integration_test.rs
use my_crate::*;

#[test]
fn test_full_workflow() {
    let result = process_data("input");
    assert!(result.is_ok());
}
```

## Configuration

Rust-specific configuration:

```toml
[project]
language = "rust"
source_paths = ["src/"]

[indexer]
excluded_dirs = [
    "target",
    ".cargo",
]

[validation]
type_check = true  # Uses cargo check
lint = true        # Uses clippy
```

## Validation with Cargo

### Cargo Check

```bash
# Enable type checking
maze config set validation.type_check true

# Generate and validate
maze generate "Create function" > src/generated.rs
cargo check
```

### Clippy Linting

```bash
# Enable linting
maze config set validation.lint true

# Generate and lint
maze generate "Create struct" > src/types.rs
cargo clippy
```

### Running Tests

```bash
# Generate tests
maze generate "Create tests for Calculator" > src/tests.rs

# Run with cargo
cargo test
```

## Style Conventions

Maze follows Rust standard style:

### Naming Conventions

- Functions: `snake_case`
- Structs/Enums/Traits: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Lifetimes: `'a`, `'b`, etc.

### Formatting

- Indentation: 4 spaces
- Line length: 100 characters
- rustfmt compatibility

## Performance

Rust indexing performance:

- **Small projects** (1K-5K LOC): ~10ms
- **Medium projects** (10K-50K LOC): ~100ms
- **Large projects** (100K+ LOC): ~1s

Symbol extraction: >800 symbols/sec ✅

## Best Practices

### Use Specific Rust Terms

```rust
// Good
prompt = "Create function returning Result<User, Error>"

// Better
prompt = """Create function:
fn find_user(id: &str) -> Result<User, DbError>
- Check database
- Return Ok(user) if found
- Return Err if not found"""
```

### Include Ownership in Prompts

```rust
prompt = "Create function process(data: &[u8]) -> Vec<u8>"  // Borrow
prompt = "Create function consume(data: String) -> String"  // Move
prompt = "Create function mutate(data: &mut Vec<i32>)"     // Mut borrow
```

### Specify Error Handling

```rust
prompt = """Create function with Result:
- Use ? operator for error propagation
- Return custom error type
- Handle edge cases"""
```

## Common Issues

### Lifetime Complexity

Start simple, add lifetimes as needed:

```rust
// Simple (no lifetimes needed)
fn process(data: String) -> String

// With borrow (needs lifetime)
fn process<'a>(data: &'a str) -> &'a str
```

### Trait Bounds

Be explicit about required traits:

```rust
prompt = "Create function requiring T: Clone + Debug"
```

### Async Runtime

Specify which async runtime:

```rust
prompt = "Create async function using tokio runtime"
prompt = "Create async function with async-std"
```

## Examples

See [examples/rust/](../../examples/rust/) for:

1. Function with Result type and error handling
2. Struct with trait implementation (Display)
3. Async function with tokio
4. Custom error type with thiserror
5. Test generation with #[test]

## Next Steps

- [Getting Started](getting-started.md) - General guide
- [Best Practices](best-practices.md) - Optimization tips
- [Provider Setup](provider-setup.md) - Configure LLM providers
- [Examples](../../examples/rust/) - Working code examples
