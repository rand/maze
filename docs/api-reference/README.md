# API Reference

Complete API documentation for Maze components.

## Core Modules

### [maze.config](config.md)

Configuration system with hierarchical TOML loading.

**Key Classes**:
- `Config` - Main configuration class
- `ProjectConfig` - Project settings
- `GenerationConfig` - Generation parameters
- `ConstraintConfig` - Constraint settings

**Usage**:
```python
from maze.config import Config

config = Config.load()  # Load from global + project
config.generation.temperature = 0.8
config.save(Path(".maze/config.toml"))
```

### [maze.core.pipeline](pipeline.md)

End-to-end pipeline orchestration.

**Key Classes**:
- `Pipeline` - Main orchestration class
- `PipelineConfig` - Pipeline configuration
- `PipelineResult` - Generation results

**Usage**:
```python
from maze.core.pipeline import Pipeline
from maze.config import Config

pipeline = Pipeline(Config())
result = pipeline.run("Create a function")
```

### [maze.logging](logging.md)

Structured logging and metrics collection.

**Key Classes**:
- `StructuredLogger` - JSON/text logging
- `MetricsCollector` - Performance metrics
- `GenerationResult` - Generation result logging
- `ValidationResult` - Validation result logging

**Usage**:
```python
from maze.logging import StructuredLogger, MetricsCollector
from maze.config import LoggingConfig

logger = StructuredLogger(LoggingConfig())
metrics = MetricsCollector()

metrics.record_latency("operation", 100.0)
summary = metrics.summary()
```

## Indexing

### [maze.indexer.base](indexer.md)

Base indexer interface and data structures.

**Key Classes**:
- `BaseIndexer` - Abstract indexer
- `IndexingResult` - Indexing results
- `Symbol` - Extracted symbol
- `StyleInfo` - Code style information

### [maze.indexer.languages.typescript](typescript-indexer.md)

TypeScript/JavaScript indexer implementation.

**Key Classes**:
- `TypeScriptIndexer` - TS/JS indexer

**Usage**:
```python
from maze.indexer.languages.typescript import TypeScriptIndexer

indexer = TypeScriptIndexer(project_path=Path("."))
result = indexer.index_directory(Path("src"))
```

## Type System

### [maze.core.types](types.md)

Type system and type inhabitation.

**Key Classes**:
- `Type` - Type representation
- `TypeContext` - Type environment
- `FunctionSignature` - Function signatures

### [maze.type_system.inhabitation](inhabitation.md)

Type inhabitation solver.

**Key Classes**:
- `InhabitationSolver` - Find paths between types

## Validation

### [maze.validation.pipeline](validation.md)

Multi-level validation pipeline.

**Key Classes**:
- `ValidationPipeline` - Orchestrates validators
- `ValidationResult` - Combined results
- `Diagnostic` - Error/warning/info

**Usage**:
```python
from maze.validation.pipeline import ValidationPipeline

validator = ValidationPipeline()
result = validator.validate(code, "typescript", context)
```

## Repair

### [maze.repair.orchestrator](repair.md)

Adaptive repair with constraint learning.

**Key Classes**:
- `RepairOrchestrator` - Repair coordination
- `RepairResult` - Repair results
- `RepairStrategy` - Strategy enum

## Learning

### [maze.learning.pattern_mining](pattern-mining.md)

Extract patterns from codebases.

**Key Classes**:
- `PatternMiner` - Pattern extraction
- `Pattern` - Extracted pattern

### [maze.learning.constraint_learning](constraint-learning.md)

Learn constraints from outcomes.

**Key Classes**:
- `ConstraintLearningSystem` - Adaptive learning
- `LearningMetrics` - Learning statistics

### [maze.learning.project_adaptation](project-adaptation.md)

Adapt to project-specific conventions.

**Key Classes**:
- `ProjectAdaptationManager` - Convention learning

### [maze.learning.feedback_orchestrator](feedback.md)

Coordinate learning across systems.

**Key Classes**:
- `FeedbackLoopOrchestrator` - Learning coordination

## Integrations

### [maze.integrations.mnemosyne](mnemosyne.md)

Persistent cross-session memory.

**Key Classes**:
- `MnemosyneIntegration` - Memory storage/recall

**Usage**:
```python
from maze.integrations.mnemosyne import MnemosyneIntegration

memory = MnemosyneIntegration()
memory.store_pattern("pattern", "namespace", importance=8)
patterns = memory.recall_patterns("query", limit=5)
```

### [maze.integrations.external](external.md)

External tool integrations (pedantic_raven, RUNE).

**Key Classes**:
- `ExternalIntegrations` - Tool coordination
- `PedanticRavenClient` - Semantic validation
- `RuneExecutor` - Sandboxed execution

## CLI

### [maze.cli.main](cli.md)

Command-line interface.

**Commands**:
- `maze init` - Initialize project
- `maze config` - Manage configuration
- `maze index` - Index codebase
- `maze generate` - Generate code
- `maze validate` - Validate code
- `maze stats` - Show statistics
- `maze debug` - Debug diagnostics

**Usage**:
```bash
maze init --language typescript
maze index .
maze generate "Create a function"
maze validate src/code.ts
```

## Benchmarking

### [maze.benchmarking](benchmarking.md)

Performance benchmarking framework.

**Key Classes**:
- `BenchmarkRunner` - Run benchmarks
- `BenchmarkSuite` - Collect results
- `BenchmarkResult` - Individual result

**Usage**:
```python
from maze.benchmarking import BenchmarkRunner, BenchmarkSuite

runner = BenchmarkRunner(config)
suite = BenchmarkSuite("My Benchmarks")

result = runner.benchmark_indexing(path, "Test")
suite.add_result(result)

suite.save(Path("results.json"))
```

## Type Annotations

Maze uses Python 3.11+ type annotations throughout:

```python
from pathlib import Path
from typing import Optional, List

def generate(
    prompt: str,
    context: Optional[TypeContext] = None
) -> PipelineResult:
    ...
```

## Error Handling

All public APIs use explicit error handling:

```python
try:
    result = pipeline.run(prompt)
except ValueError as e:
    # Configuration or input error
    print(f"Invalid input: {e}")
except Exception as e:
    # Unexpected error
    print(f"Error: {e}")
```

## Performance Monitoring

### Metrics Collection

```python
pipeline = Pipeline(config)
pipeline.run(prompt)

# Get metrics
summary = pipeline.metrics.summary()

print(f"Latencies: {summary['latencies']}")
print(f"Cache hit rates: {summary['cache_hit_rates']}")
print(f"Errors: {summary['errors']}")
```

### Prometheus Export

```python
metrics_text = pipeline.metrics.export_prometheus()

# Serve on HTTP endpoint
# Scrape with Prometheus
```

## Extension Points

### Custom Indexer

```python
from maze.indexer.base import BaseIndexer

class MyLanguageIndexer(BaseIndexer):
    def index_file(self, path: Path) -> IndexingResult:
        # Implement language-specific indexing
        ...
```

### Custom Validator

```python
from maze.validation.pipeline import ValidationPipeline

class CustomValidator:
    def validate(self, code: str) -> ValidationResult:
        # Custom validation logic
        ...

pipeline = ValidationPipeline(
    custom_validator=CustomValidator()
)
```

## See Also

- **[Getting Started](../user-guide/getting-started.md)** - Quick start guide
- **[Core Concepts](../user-guide/core-concepts.md)** - System concepts
- **[Architecture](../architecture.md)** - System design
- **[Examples](../../examples/)** - Working examples
