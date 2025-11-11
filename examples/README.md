# Maze Examples

This directory contains working examples demonstrating Maze's capabilities for adaptive constrained code generation.

## Basic Examples - TypeScript

Simple, focused examples demonstrating core features:

1. **[01-function-generation.py](typescript/01-function-generation.py)** - Generate type-safe functions with validation
2. **[02-class-generation.py](typescript/02-class-generation.py)** - Generate classes with properties and methods
3. **[03-interface-generation.py](typescript/03-interface-generation.py)** - Generate interfaces with generics
4. **[04-api-endpoint.py](typescript/04-api-endpoint.py)** - Generate REST API endpoints
5. **[05-type-safe-refactor.py](typescript/05-type-safe-refactor.py)** - Refactor code with type safety

## Basic Examples - Python

Python-specific examples:

1. **[01-function-generation.py](python/01-function-generation.py)** - Function with type hints and validation
2. **[02-dataclass.py](python/02-dataclass.py)** - Dataclass with __post_init__ validation
3. **[03-async-function.py](python/03-async-function.py)** - Async/await with error handling
4. **[04-fastapi-endpoint.py](python/04-fastapi-endpoint.py)** - FastAPI endpoint with Pydantic
5. **[05-test-generation.py](python/05-test-generation.py)** - Pytest test generation

## Advanced Examples

Complex real-world scenarios:

1. **[01-api-generation.py](advanced/01-api-generation.py)** - Generate complete REST API from OpenAPI schema
2. **[02-code-refactoring.py](advanced/02-code-refactoring.py)** - Refactor legacy code to modern TypeScript
3. **[03-test-generation.py](advanced/03-test-generation.py)** - Generate comprehensive test suites

## Integration Examples

Production workflow integrations:

1. **[01-github-bot.py](integration/01-github-bot.py)** - GitHub code review bot pattern
2. **[02-ci-pipeline.py](integration/02-ci-pipeline.py)** - CI/CD integration example

## Running Examples

All examples can be run directly with Python:

```bash
# Basic examples
python examples/typescript/01-function-generation.py

# Advanced examples
python examples/advanced/01-api-generation.py

# Integration examples
python examples/integration/01-github-bot.py
```

## Testing Examples

Run the test suite to verify all examples work:

```bash
# Test all examples
uv run pytest tests/unit/test_examples/test_examples.py -v

# Test specific category
uv run pytest tests/unit/test_examples/test_examples.py::TestBasicExamples -v
```

## Example Structure

Each example demonstrates:
- **Problem**: What code to generate
- **Configuration**: Maze configuration for the task
- **Pipeline Usage**: Using Maze programmatically
- **Results**: Generated code and metrics
- **Validation**: Code validation results

## Key Features Demonstrated

- **Type Constraints**: Enforcing type safety during generation
- **Syntactic Constraints**: Grammar-based code structure
- **Validation Pipeline**: Multi-level validation (syntax, types, tests)
- **Metrics Collection**: Performance tracking
- **Error Handling**: Graceful degradation
- **Configuration**: Hierarchical configuration management

## Next Steps

After running examples, see:
- [User Guide](../docs/user-guide/getting-started.md) - Comprehensive tutorials
- [API Reference](../docs/api-reference/) - Complete API documentation
- [Architecture Guide](../docs/architecture.md) - System design details
