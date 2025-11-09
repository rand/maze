# Contributing to Maze

Thank you for your interest in contributing to Maze! This document provides guidelines for contributing to the project.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/maze.git
   cd maze
   ```
3. **Set up development environment**:
   ```bash
   uv pip install -e ".[dev]"
   ```

## Development Workflow

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

Use prefixes:
- `feature/` - New features
- `fix/` - Bug fixes
- `refactor/` - Code refactoring
- `docs/` - Documentation updates
- `perf/` - Performance improvements

### 2. Follow the Work Plan Protocol

Maze follows a **4-phase Work Plan Protocol**. See [CLAUDE.md](CLAUDE.md) for detailed guidelines:

1. **Prompt → Spec**: Clarify requirements, identify constraints
2. **Spec → Full Spec**: Design constraint hierarchy, plan type system
3. **Full Spec → Plan**: Sequence pipeline stages, identify parallelization
4. **Plan → Artifacts**: Implement with mandatory benchmarks

### 3. Code Standards

#### Performance Requirements (MANDATORY)

**All constraint implementations must include performance benchmarks:**

```python
@pytest.mark.performance
def test_your_constraint_performance():
    """Validate constraint meets <100μs target."""
    # See CLAUDE.md for benchmark template
    times = benchmark_constraint(your_constraint)
    p99 = statistics.quantiles(times, n=100)[98]
    assert p99 < 100, f"P99 {p99:.1f}μs exceeds 100μs target"
```

#### Code Quality

- **Formatting**: Run `uv run black src/ tests/`
- **Linting**: Run `uv run ruff src/ tests/`
- **Type Checking**: Run `uv run mypy src/`
- **Tests**: Run `uv run pytest tests/unit -v`

### 4. Testing Requirements

#### Coverage Targets
- Core type system: **90%+**
- Constraint synthesis: **85%+**
- Indexers: **80%+ per language**
- LLGuidance adapter: **85%+**

#### Test Categories
```bash
# Unit tests (fast)
uv run pytest tests/unit -v

# Performance benchmarks (mandatory for constraints)
uv run pytest -m performance -v

# Integration tests
uv run pytest tests/integration -v

# End-to-end tests
uv run pytest tests/e2e -v
```

### 5. Commit Guidelines

#### Commit Messages

**Good commits** describe what and why:
```bash
git commit -m "Optimize grammar caching for TypeScript (p99: 120μs → 45μs)

- Increased LRU cache size from 100k to 200k
- Added grammar content hashing for better cache keys
- Measured 89% cache hit rate (previous: 72%)
"
```

**Bad commits** are vague:
```bash
git commit -m "changes"  # ❌ Too vague
git commit -m "wip"      # ❌ Not meaningful
git commit -m "fixed"    # ❌ What was fixed?
```

#### Commit Before Testing

**CRITICAL**: Always commit changes before running tests:

```bash
# 1. Commit changes
git add . && git commit -m "Implement feature X"

# 2. Run tests
uv run pytest

# 3. If tests fail, fix and commit again
git add . && git commit -m "Fix test failures in feature X"
```

### 6. Performance Validation

**Before marking work complete**, validate performance:

```bash
# Run all performance benchmarks
uv run pytest -m performance -v

# Run specific benchmarks
uv run python benchmarks/mask_computation.py

# Check metrics are within targets
# - Token mask: <100μs (p99)
# - Grammar compilation: <50ms
# - Cache hit rate: >70%
```

### 7. Documentation

#### Update Documentation When:
- Adding new constraint types
- Implementing new language indexers
- Adding provider adapters
- Changing performance characteristics
- Adding integration points

#### Documentation Files
- `README.md` - User-facing documentation
- `CLAUDE.md` - Developer guidelines (project-specific)
- `docs/` - Detailed documentation (architecture, API, guides)
- Docstrings - All public APIs must have docstrings

### 8. Beads Task Management

Track your work in Beads:

```bash
# Create task for your feature
bd create "Implement Python indexer" -t task -p 1 --json

# Update progress
bd update <issue-id> --status in_progress --json
bd update <issue-id> --comment "Symbol extraction complete" --json

# Complete when done
bd close <issue-id> --reason "Complete" --json
```

### 9. Pull Request Process

#### Before Submitting

✅ **Checklist**:
- [ ] Code formatted (`black`, `ruff`)
- [ ] Type checking passes (`mypy`)
- [ ] All tests pass
- [ ] Performance benchmarks pass (if applicable)
- [ ] Coverage targets met
- [ ] Documentation updated
- [ ] CHANGELOG.md updated (if applicable)
- [ ] Beads issue updated/closed

#### Create Pull Request

```bash
# Push branch
git push -u origin feature/your-feature-name

# Create PR using GitHub CLI
gh pr create --title "Add Python indexer" \
  --body "$(cat <<'EOF'
## Summary
- Implemented Python code indexer using Pyright
- Added symbol extraction for functions, classes, type aliases
- Integrated with tree-sitter-python for fast parsing

## Performance
- Indexing speed: 1200 symbols/sec
- Memory usage: 150MB for 10k LOC
- Benchmark: `uv run pytest tests/unit/test_indexer/test_python.py -v`

## Test Plan
- [x] Unit tests for symbol extraction
- [x] Integration test with Pyright
- [x] Performance benchmark
- [x] Type checking passes

## Dependencies
- Added pyright>=1.1.350
- Added tree-sitter-python>=0.20.4
EOF
)"
```

#### PR Review Process

1. **Automated Checks**: CI/CD runs tests, benchmarks, linting
2. **Code Review**: Maintainers review code quality, architecture
3. **Performance Review**: Validate benchmarks meet targets
4. **Documentation Review**: Ensure docs are complete and accurate
5. **Approval**: At least one maintainer approval required
6. **Merge**: Squash and merge to main

### 10. Integration Guidelines

When integrating with external systems:

#### llguidance
- Follow grammar design principles in CLAUDE.md
- Ensure <100μs mask computation
- Test with actual LLM providers, not mocks
- Document grammar optimizations

#### mnemosyne
- Use proper namespacing: `project:maze:*`
- Set appropriate importance levels (8-10 for critical patterns)
- Store both successes and failures for learning
- Include context and metadata

#### pedantic_raven
- Define clear property specifications
- Use appropriate validation mode (strict/moderate/lenient)
- Document semantic constraints

#### RUNE
- Set reasonable resource limits
- Use isolated sandboxes for safety
- Extract diagnostics for repair loop

## Anti-Patterns to Avoid

See [CLAUDE.md](CLAUDE.md) for complete list. Critical violations:

```
❌ Skip performance benchmarks for constraints
❌ Ignore cache hit rates <70%
❌ Allow mask computation >100μs
❌ Hard-code language-specific logic (use indexers)
❌ Test before committing
❌ Skip mnemosyne integration for learned patterns
```

## Getting Help

- **Documentation**: See [CLAUDE.md](CLAUDE.md) for detailed guidelines
- **Issues**: Open a GitHub issue for bugs or feature requests
- **Discussions**: Use GitHub Discussions for questions
- **Architecture**: See `docs/architecture.md`
- **API Reference**: See `docs/api-reference.md`

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on the code, not the person
- Assume good intentions
- Help others learn and grow

## Recognition

Contributors will be recognized in:
- `CONTRIBUTORS.md` file
- Release notes for significant contributions
- Project documentation

Thank you for contributing to Maze! 🎉