# Getting Started with Maze

Maze is an adaptive constrained code generation system that produces **faster, more correct code** by combining LLMs with formal constraint enforcement.

## Installation

```bash
# Install from PyPI (when published)
pip install maze-codegen

# Or install from source
git clone https://github.com/rand/maze
cd maze
uv sync
```

## Provider Setup

Maze requires an LLM provider for code generation. Set up OpenAI (recommended):

```bash
# Get API key from https://platform.openai.com
export OPENAI_API_KEY=sk-your-key-here

# Verify it works
maze generate "Create a hello world function"
```

See [Provider Setup Guide](provider-setup.md) for other providers (vLLM, SGLang, llama.cpp).

## Quick Start (5 minutes)

### 1. Initialize a Project

```bash
# Create new Maze project
maze init --language typescript

# This creates:
# .maze/
#   config.toml    # Project configuration
#   cache/         # Indexing cache
```

### 2. Index Your Codebase

```bash
# Index project to extract context
maze index .

# This extracts:
# - Type signatures and interfaces
# - Function signatures
# - Code patterns and conventions
# - Test patterns
```

### 3. Generate Code

```bash
# Generate a function
maze generate "Create a function to validate email addresses"

# Generate with specific constraints
maze generate "Create async API endpoint" --constraints type syntactic
```

### 4. Validate Generated Code

```bash
# Validate a file
maze validate src/generated.ts

# Validate with auto-fix
maze validate src/generated.ts --fix
```

## Your First Generation

Let's generate a type-safe TypeScript function:

```python
from maze.config import Config
from maze.core.pipeline import Pipeline

# Configure Maze
config = Config()
config.project.language = "typescript"
config.constraints.type_enabled = True

# Create pipeline
pipeline = Pipeline(config)

# Generate code
result = pipeline.run("Create a function to calculate fibonacci numbers")

# Check result
if result.success:
    print(result.code)
    print(f"✅ Generated in {result.total_duration_ms:.0f}ms")
else:
    print(f"❌ Failed: {result.errors}")

pipeline.close()
```

## Core Concepts

### Constraints (4-Tier System)

Maze uses a hierarchical constraint system:

1. **Syntactic Constraints**: CFG grammars ensure valid syntax
2. **Type Constraints**: Type inhabitation ensures type safety
3. **Semantic Constraints**: Tests and properties ensure correctness
4. **Contextual Constraints**: Project patterns ensure consistency

### Pipeline Workflow

```
Index Project → Synthesize Constraints → Generate Code → Validate → Repair (if needed)
```

### Configuration

Configuration follows a hierarchy:

1. **Global**: `~/.config/maze/config.toml`
2. **Project**: `.maze/config.toml`
3. **CLI args**: Override both

Example config:

```toml
[project]
name = "my-project"
language = "typescript"
source_paths = ["src/", "lib/"]

[generation]
provider = "openai"
model = "gpt-4"
temperature = 0.7

[constraints]
syntactic_enabled = true
type_enabled = true
semantic_enabled = false
contextual_enabled = true
```

## Performance Targets

Maze is designed for speed:

- **Token mask computation**: <100μs (p99)
- **Grammar compilation**: <50ms
- **Indexing**: <30s for 100K LOC
- **Generation**: <10s per prompt

Actual performance (from benchmarks):

- **Indexing**: 190ms for 100K LOC ✅ (157x faster than target)
- **Generation**: 2.2s average ✅ (4.5x faster than target)
- **Memory**: 31MB peak ✅ (64x under budget)

## What's Next?

- **[Core Concepts](core-concepts.md)**: Deep dive into constraint types
- **[Tutorials](tutorials/)**: Step-by-step guides
- **[Best Practices](best-practices.md)**: Tips for optimal results
- **[API Reference](../api-reference/)**: Complete API documentation
- **[Examples](../../examples/)**: Working code examples

## Getting Help

- **Documentation**: https://maze.dev/docs
- **GitHub Issues**: https://github.com/rand/maze/issues
- **Examples**: See [examples/](../../examples/) directory

## Common Commands

```bash
# Project management
maze init                          # Initialize project
maze config list                   # Show configuration
maze config set KEY VALUE          # Update config

# Code operations
maze index                         # Index project
maze generate PROMPT               # Generate code
maze validate FILE                 # Validate code

# Monitoring
maze stats                         # Show statistics
maze debug --verbose               # Debug info
```
