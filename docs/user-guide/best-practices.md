# Best Practices

Guidelines for getting the best results from Maze.

## Constraint Selection

### Start Simple, Add Complexity

```python
# Start with syntactic only for rapid prototyping
config.constraints.syntactic_enabled = True
config.constraints.type_enabled = False

# Add types when code stabilizes
config.constraints.type_enabled = True

# Add semantic constraints for critical code
config.constraints.semantic_enabled = True
```

### Match Constraints to Task

| Task Type | Recommended Constraints | Rationale |
|-----------|------------------------|-----------|
| Boilerplate generation | Syntactic + Contextual | Fast, matches project style |
| API endpoints | Syntactic + Type | Type safety critical |
| Algorithm implementation | All 4 tiers | Correctness critical |
| Test generation | Syntactic + Type + Semantic | Must match test patterns and pass |
| Refactoring | Syntactic + Type + Contextual | Preserve types and style |

## Performance Optimization

### Cache Warming

```bash
# Index project once, reuse for multiple generations
maze index .

# Cache persists between sessions
```

### Batch Operations

```python
# Reuse pipeline instance for multiple generations
pipeline = Pipeline(config)

for prompt in prompts:
    result = pipeline.generate(prompt)
    # Process result

pipeline.close()
```

### Tune Cache Size

```python
# For large projects
config.performance.cache_size = 200_000  # Default: 100k

# Monitor cache hit rate
maze stats --show-cache
# Target: >70% hit rate
```

## Type Safety

### Provide Rich Context

```python
# Index project before generation
pipeline.index_project()

# Types extracted guide generation toward correct expressions
```

### Use Type Hints in Prompts

```python
# Good: Specific types
prompt = "Create function: (user: User) => string"

# Better: Include return type
prompt = "Create function validateEmail(email: string): boolean"
```

### Enable Type Checking

```python
config.validation.type_check = True

# Catches type errors early
```

## Prompt Engineering

### Be Specific

```python
# ❌ Vague
"Create a function"

# ✅ Specific
"Create a TypeScript function 'calculateTax' that takes price (number) and rate (number), returns number, validates inputs"
```

### Include Examples

```python
prompt = """Create array sorting function.

Example:
Input: [3, 1, 2]
Output: [1, 2, 3]

Handle: empty arrays, single element, duplicates"""
```

### Specify Constraints in Prompt

```python
prompt = """Create async function with:
- Error handling using try/catch
- Return type: Promise<Result>
- Input validation
- TypeScript strict mode compatible"""
```

## Validation Strategy

### Enable Relevant Validators

```python
# For type-safe code
config.validation.syntax_check = True
config.validation.type_check = True

# For production code
config.validation.run_tests = True
config.validation.lint = True
```

### Handle Validation Failures

```python
result = pipeline.run(prompt)

if not result.success:
    if result.validation:
        # Inspect errors
        for error in result.validation.errors:
            print(f"Line {error.line}: {error.message}")
    
    # Repair can fix many issues
    if result.repair:
        print(f"Fixed in {result.repair.attempts} attempts")
```

## Adaptive Learning

### Let Maze Learn from Your Project

```python
# Enable contextual constraints
config.constraints.contextual_enabled = True

# Maze will learn:
# - Naming conventions
# - Code organization patterns
# - Error handling styles
# - Testing approaches
```

### Store Successful Patterns

Maze automatically stores successful patterns in mnemosyne:

```python
# Patterns stored after successful generation
# Retrieved for similar future tasks
# Weighted by success rate
```

### Monitor Learning Progress

```bash
# Check learned patterns
maze stats --show-patterns

# Reset learning if needed
maze learn reset --confirm
```

## Error Handling

### Graceful Degradation

Maze continues working even when optional tools unavailable:

```python
# Works without pedantic_raven
# Works without RUNE
# Works without mnemosyne

# Check availability:
maze debug  # Shows which tools available
```

### Handle Repair Failures

```python
config.constraints.adaptive_weighting = True

result = pipeline.run(prompt)

if not result.success:
    # Check repair attempts
    if result.repair and result.repair.attempts >= 3:
        # Repair exhausted, may need manual intervention
        print("Manual fix required")
```

## Memory Management

### For Large Codebases

```python
# Limit file size
config.indexer.max_file_size_kb = 500  # Skip huge files

# Exclude directories
config.indexer.excluded_dirs = [
    "node_modules",
    "dist",
    "coverage",
    ".git"
]

# Disable incremental if memory constrained
config.indexer.incremental = False
```

### Monitor Memory Usage

```bash
# Check memory metrics
maze stats --show-performance

# Profile memory
python benchmarks/phase6/run_benchmarks.py --category stress
```

## Multi-Language Projects

### Configure Per-Language

```python
# TypeScript files
ts_config = Config()
ts_config.project.language = "typescript"
ts_pipeline = Pipeline(ts_config)

# Python files
py_config = Config()
py_config.project.language = "python"
py_pipeline = Pipeline(py_config)
```

### Language Detection

Currently supported:
- TypeScript/JavaScript (full support)
- Python (planned Phase 6+)
- Rust (planned)
- Go (planned)
- Zig (planned)

## Production Deployment

### Environment Variables

```bash
# Provider API keys
export OPENAI_API_KEY=sk-...
export ANTHROPIC_API_KEY=sk-...

# Configuration
export MAZE_CONFIG_PATH=/etc/maze/config.toml
```

### Logging Configuration

```python
config.logging.format = "json"  # For structured logging
config.logging.log_file = Path("/var/log/maze/app.log")
config.logging.metrics_enabled = True
```

### Metrics Export

```python
from maze.logging import MetricsCollector

collector = MetricsCollector()

# Export for Prometheus
metrics_text = collector.export_prometheus()

# Expose on /metrics endpoint
```

## Common Patterns

### Generate and Save

```python
result = pipeline.run(prompt)

if result.success:
    output_path = Path("generated.ts")
    output_path.write_text(result.code)
    print(f"✅ Saved to {output_path}")
```

### Validate Before Committing

```python
# Generate
result = pipeline.run(prompt)

# Validate thoroughly
validation = pipeline.validate(result.code)

if validation.success:
    # Safe to commit
    subprocess.run(["git", "add", "generated.ts"])
    subprocess.run(["git", "commit", "-m", "Add generated code"])
```

### Iterative Refinement

```python
prompt = "Create function"
result = pipeline.run(prompt)

# Not satisfied? Refine
refined_prompt = f"{prompt}. Add error handling and validation."
result = pipeline.run(refined_prompt)
```

## Troubleshooting

### Slow Generation

```python
# Check metrics
maze stats --show-performance

# Common causes:
# - Large project (optimize indexing)
# - Complex type search (reduce depth)
# - Semantic validation enabled (disable if not needed)
```

### Low Cache Hit Rate

```bash
# Check cache stats
maze stats --show-cache

# If <70%:
# - Increase cache size
# - Check grammar variation
# - Enable incremental indexing
```

### Type Errors

```python
# Enable type checking in validation
config.validation.type_check = True

# Increase type search depth
config.constraints.type_search_depth = 10

# Provide more context
pipeline.index_project()  # Ensure indexed
```

## Next Steps

- **[Tutorials](tutorials/)**: Step-by-step guides
- **[API Reference](../api-reference/)**: Complete API
- **[Architecture](../architecture.md)**: Deep dive into internals
