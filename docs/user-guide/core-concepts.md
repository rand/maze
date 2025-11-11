# Core Concepts

Understanding Maze's constraint-based approach to code generation.

## The 4-Tier Constraint System

Maze uses a hierarchical constraint system that progressively narrows the generation space:

### 1. Syntactic Constraints (Tier 1)

**Purpose**: Ensure valid syntax using Context-Free Grammars (CFG)

**How it works**:
- Lark grammars define valid syntax for each language
- llguidance compiles grammars into token masks
- Invalid tokens are blocked during generation

**Performance**: <100μs per token (p99)

**Example**:
```python
config.constraints.syntactic_enabled = True

# Grammar ensures only valid TypeScript syntax
# Blocks: incomplete statements, mismatched braces, etc.
```

### 2. Type Constraints (Tier 2)

**Purpose**: Ensure type safety using type inhabitation

**How it works**:
- Type system extracts types from project context
- Type inhabitation solver finds paths: source type → target type
- Generation biased toward type-correct expressions

**Performance**: <1ms per type search (p95)

**Example**:
```python
config.constraints.type_enabled = True

# Given: user: User, need: string
# Solver finds: user.name, user.email, user.toString()
# Blocks: user.age (if age is number), invalid property access
```

### 3. Semantic Constraints (Tier 3)

**Purpose**: Ensure behavioral correctness using tests and properties

**How it works**:
- Tests specify expected behavior
- Property-based constraints define invariants
- Generated code validated against tests in RUNE sandbox

**Performance**: <500ms per validation

**Example**:
```python
config.constraints.semantic_enabled = True

# Constraint: "Function must sort ascending"
# Tests: sort([3,1,2]) == [1,2,3]
# Properties: output.length == input.length, is_sorted(output)
```

### 4. Contextual Constraints (Tier 4)

**Purpose**: Match project patterns and conventions (soft constraints)

**How it works**:
- Pattern mining extracts common idioms from codebase
- Constraints weighted by frequency and success rate
- Applied as logit bias, not hard constraints

**Performance**: <50ms pattern mining, <10ms application

**Example**:
```python
config.constraints.contextual_enabled = True

# Learns from project:
# - Naming: camelCase vs snake_case
# - Async: async/await vs promises
# - Error handling: try/catch patterns
# - Style: semicolons, quotes, indentation
```

## Pipeline Architecture

```
┌─────────────┐
│   Index     │  Extract symbols, types, patterns
│   Project   │  Performance: <30s for 100K LOC
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Synthesize  │  Build constraints from context
│ Constraints │  Performance: <50ms
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Generate   │  LLM generation with constraints
│    Code     │  Performance: <10s per prompt
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Validate   │  Multi-level validation
│    Code     │  Performance: <500ms
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Repair    │  Fix errors with constraint refinement
│  (if needed)│  Max attempts: 3, Avg convergence: 2.1
└─────────────┘
```

## Type System

### Type Inhabitation

Type inhabitation finds paths from source type to target type:

```typescript
// Given context:
interface User {
    id: string;
    name: string;
    profile: Profile;
}

interface Profile {
    bio: string;
    age: number;
}

// Problem: user: User → need: string
// Solutions:
// - user.id (direct)
// - user.name (direct)
// - user.profile.bio (traversal)
// - user.toString() (method)
```

### Bidirectional Type Inference

Maze infers types in both directions:

- **Synthesis**: Infer type from expression
  - `user.name` → `string`
- **Checking**: Verify expression matches expected type
  - `user.age` against `string` → fails

### Generic Types

Full support for generics:

```typescript
Repository<T>
Promise<T | null>
Array<User>
Record<string, T>
```

## Adaptive Learning

Maze learns from successes and failures to improve over time:

### Pattern Mining

Extracts reusable patterns from codebase:
- Function signatures
- Class structures
- Error handling idioms
- Testing patterns

### Constraint Learning

Learns which constraints work best:
- Successful patterns → boosted weight
- Failed patterns → reduced weight
- Stored in mnemosyne for cross-session learning

### Project Adaptation

Adapts to project-specific conventions:
- Naming conventions
- Code organization
- Style preferences
- Testing approaches

## External Integrations

### mnemosyne (Pattern Storage)

Persistent memory across sessions:

```bash
# Patterns stored automatically during generation
# Recalled when similar context detected
# Evolution: consolidation, decay, archival
```

### pedantic_raven (Semantic Validation)

Deep semantic analysis (optional):

```python
# Validates properties beyond syntax/types
# Property-based testing integration
# Behavioral correctness checks
```

### RUNE (Sandboxed Execution)

Safe code execution (optional):

```python
# Network isolation
# Filesystem isolation
# Resource limits (CPU, memory, time)
# Deterministic execution
```

## Performance Model

### Token-Level Efficiency

Every token generation involves:

1. **Compute mask** (<100μs): Which tokens are valid?
2. **Sample token** (LLM inference): Pick from valid tokens
3. **Update state** (<10μs): Advance parser

Total overhead: **<100μs per token** (50μs achieved)

### Cache Strategy

Multi-level caching:

- **Grammar cache**: Compiled grammars (>70% hit rate)
- **Type cache**: Type inhabitation paths
- **Pattern cache**: Mnemosyne patterns
- **AST cache**: Parsed file structures

## Best Practices

### When to Use Which Constraints

| Task | Syntactic | Type | Semantic | Contextual |
|------|-----------|------|----------|------------|
| Quick prototyping | ✅ | ❌ | ❌ | ❌ |
| Production code | ✅ | ✅ | ❌ | ✅ |
| Critical systems | ✅ | ✅ | ✅ | ✅ |
| Refactoring | ✅ | ✅ | ❌ | ✅ |
| Test generation | ✅ | ✅ | ✅ | ✅ |

### Performance Tuning

For faster generation:
```python
config.constraints.semantic_enabled = False  # Skip slow tests
config.performance.cache_size = 200_000      # Larger cache
config.generation.temperature = 0.5          # More deterministic
```

For better quality:
```python
config.constraints.type_search_depth = 10    # Deeper type search
config.constraints.semantic_enabled = True   # Enable tests
config.validation.run_tests = True           # Run actual tests
```

## Next Steps

- **[Tutorials](tutorials/)**: Step-by-step guides
- **[Best Practices](best-practices.md)**: Optimization tips
- **[API Reference](../api-reference/)**: Complete API docs
- **[Architecture](../architecture.md)**: System design
