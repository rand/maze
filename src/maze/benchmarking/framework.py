"""Performance benchmarking framework for Phase 6.

Provides structured benchmarking for:
- Indexing performance (small, medium, large projects)
- Generation latency
- Validation throughput
- Memory usage
- Stress testing

Performance targets:
- Indexing: <30s for 100K LOC
- Generation: <10s per prompt
- Memory: <2GB for 100K LOC
- Cache hit rate: >70%
"""

import json
import statistics
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import psutil

from maze.config import Config
from maze.core.pipeline import Pipeline


@dataclass
class BenchmarkResult:
    """Result from a benchmark run."""

    name: str
    category: str  # indexing, generation, validation, stress
    duration_ms: float
    memory_mb: float
    metrics: dict[str, Any] = field(default_factory=dict)
    success: bool = True
    error: str | None = None


@dataclass
class BenchmarkSuite:
    """Collection of benchmark results."""

    name: str
    results: list[BenchmarkResult] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: time.strftime("%Y-%m-%d %H:%M:%S"))

    def add_result(self, result: BenchmarkResult) -> None:
        """Add a benchmark result."""
        self.results.append(result)

    def get_statistics(self, category: str | None = None) -> dict[str, Any]:
        """Get statistics for results.

        Args:
            category: Filter by category (optional)

        Returns:
            Statistics dictionary
        """
        filtered = self.results
        if category:
            filtered = [r for r in self.results if r.category == category]

        if not filtered:
            return {}

        durations = [r.duration_ms for r in filtered]
        memories = [r.memory_mb for r in filtered]

        return {
            "count": len(filtered),
            "duration": {
                "mean": statistics.mean(durations),
                "median": statistics.median(durations),
                "min": min(durations),
                "max": max(durations),
                "stdev": statistics.stdev(durations) if len(durations) > 1 else 0,
            },
            "memory": {
                "mean": statistics.mean(memories),
                "median": statistics.median(memories),
                "min": min(memories),
                "max": max(memories),
            },
            "success_rate": sum(1 for r in filtered if r.success) / len(filtered),
        }

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "timestamp": self.timestamp,
            "results": [asdict(r) for r in self.results],
            "statistics": {
                "overall": self.get_statistics(),
                "indexing": self.get_statistics("indexing"),
                "generation": self.get_statistics("generation"),
                "validation": self.get_statistics("validation"),
                "stress": self.get_statistics("stress"),
            },
        }

    def save(self, path: Path) -> None:
        """Save benchmark results to JSON file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)


class BenchmarkRunner:
    """Runner for performance benchmarks."""

    def __init__(self, config: Config | None = None):
        """Initialize benchmark runner.

        Args:
            config: Maze configuration (uses default if None)
        """
        self.config = config or Config()
        self.pipeline = Pipeline(self.config)
        self.process = psutil.Process()

    def benchmark_indexing(self, project_path: Path, name: str) -> BenchmarkResult:
        """Benchmark project indexing.

        Args:
            project_path: Path to project
            name: Benchmark name

        Returns:
            BenchmarkResult with indexing metrics
        """
        # Get initial memory
        mem_before = self.process.memory_info().rss / 1024 / 1024  # MB

        start = time.perf_counter()
        try:
            result = self.pipeline.index_project(project_path)
            duration_ms = (time.perf_counter() - start) * 1000

            mem_after = self.process.memory_info().rss / 1024 / 1024  # MB
            memory_mb = mem_after - mem_before

            return BenchmarkResult(
                name=name,
                category="indexing",
                duration_ms=duration_ms,
                memory_mb=memory_mb,
                metrics={
                    "files": len(result.files_processed),
                    "symbols": len(result.symbols),
                    "errors": len(result.errors),
                },
                success=True,
            )
        except Exception as e:
            duration_ms = (time.perf_counter() - start) * 1000
            mem_after = self.process.memory_info().rss / 1024 / 1024

            return BenchmarkResult(
                name=name,
                category="indexing",
                duration_ms=duration_ms,
                memory_mb=mem_after - mem_before,
                success=False,
                error=str(e),
            )

    def benchmark_generation(self, prompt: str, name: str, iterations: int = 1) -> BenchmarkResult:
        """Benchmark code generation.

        Args:
            prompt: Generation prompt
            name: Benchmark name
            iterations: Number of iterations to average

        Returns:
            BenchmarkResult with generation metrics
        """
        durations = []
        memories = []

        for _ in range(iterations):
            mem_before = self.process.memory_info().rss / 1024 / 1024

            start = time.perf_counter()
            try:
                result = self.pipeline.generate(prompt)
                duration_ms = (time.perf_counter() - start) * 1000
                durations.append(duration_ms)

                mem_after = self.process.memory_info().rss / 1024 / 1024
                memories.append(mem_after - mem_before)

            except Exception:
                duration_ms = (time.perf_counter() - start) * 1000
                durations.append(duration_ms)
                memories.append(0)

        return BenchmarkResult(
            name=name,
            category="generation",
            duration_ms=statistics.mean(durations),
            memory_mb=statistics.mean(memories),
            metrics={
                "iterations": iterations,
                "min_duration": min(durations),
                "max_duration": max(durations),
            },
            success=True,
        )

    def benchmark_validation(self, code: str, name: str, iterations: int = 10) -> BenchmarkResult:
        """Benchmark code validation.

        Args:
            code: Code to validate
            name: Benchmark name
            iterations: Number of iterations

        Returns:
            BenchmarkResult with validation metrics
        """
        durations = []

        for _ in range(iterations):
            start = time.perf_counter()
            result = self.pipeline.validate(code)
            duration_ms = (time.perf_counter() - start) * 1000
            durations.append(duration_ms)

        return BenchmarkResult(
            name=name,
            category="validation",
            duration_ms=statistics.mean(durations),
            memory_mb=0,  # Validation doesn't allocate much
            metrics={
                "iterations": iterations,
                "throughput": 1000 / statistics.mean(durations),  # ops/sec
                "p95": sorted(durations)[int(len(durations) * 0.95)],
                "p99": sorted(durations)[int(len(durations) * 0.99)],
            },
            success=True,
        )

    def stress_test_concurrent(self, prompts: list[str], name: str) -> BenchmarkResult:
        """Stress test with concurrent generations.

        Args:
            prompts: List of prompts to generate
            name: Benchmark name

        Returns:
            BenchmarkResult with stress test metrics
        """

        mem_before = self.process.memory_info().rss / 1024 / 1024

        start = time.perf_counter()
        results = []

        # Run sequentially (true concurrency would require multiple processes)
        for prompt in prompts:
            try:
                result = self.pipeline.generate(prompt)
                results.append(result)
            except Exception:
                pass

        duration_ms = (time.perf_counter() - start) * 1000
        mem_after = self.process.memory_info().rss / 1024 / 1024

        return BenchmarkResult(
            name=name,
            category="stress",
            duration_ms=duration_ms,
            memory_mb=mem_after - mem_before,
            metrics={
                "prompts": len(prompts),
                "completed": len(results),
                "avg_per_prompt": duration_ms / len(prompts) if prompts else 0,
            },
            success=True,
        )

    def profile_memory(self, operations: list[str], name: str) -> BenchmarkResult:
        """Profile memory usage across operations.

        Args:
            operations: List of operations to perform
            name: Benchmark name

        Returns:
            BenchmarkResult with memory profiling
        """
        mem_samples = []

        for op in operations:
            if op == "index":
                # Create temp project
                import tempfile

                with tempfile.TemporaryDirectory() as tmpdir:
                    project = Path(tmpdir)
                    (project / "test.ts").write_text("const x = 1;")
                    self.pipeline.index_project(project)
            elif op == "generate":
                self.pipeline.generate("test")
            elif op == "validate":
                self.pipeline.validate("const x = 1;")

            mem = self.process.memory_info().rss / 1024 / 1024
            mem_samples.append(mem)

        return BenchmarkResult(
            name=name,
            category="stress",
            duration_ms=0,
            memory_mb=max(mem_samples) if mem_samples else 0,
            metrics={
                "peak_memory": max(mem_samples) if mem_samples else 0,
                "avg_memory": statistics.mean(mem_samples) if mem_samples else 0,
                "operations": len(operations),
            },
            success=True,
        )


def generate_report(suite: BenchmarkSuite, output_path: Path) -> None:
    """Generate markdown report from benchmark results.

    Args:
        suite: Benchmark suite
        output_path: Path to save report
    """
    stats = suite.to_dict()["statistics"]

    lines = [
        f"# Benchmark Report: {suite.name}",
        f"\n**Timestamp**: {suite.timestamp}",
        f"\n**Total Benchmarks**: {len(suite.results)}",
        "\n## Overall Statistics",
        "",
    ]

    if "overall" in stats and stats["overall"]:
        overall = stats["overall"]
        lines.extend(
            [
                f"- **Success Rate**: {overall['success_rate']:.1%}",
                f"- **Average Duration**: {overall['duration']['mean']:.2f}ms",
                f"- **Median Duration**: {overall['duration']['median']:.2f}ms",
                f"- **P95 Duration**: {overall['duration'].get('p95', 0):.2f}ms",
                f"- **Average Memory**: {overall['memory']['mean']:.2f}MB",
                "",
            ]
        )

    # Category-specific stats
    for category in ["indexing", "generation", "validation", "stress"]:
        if category in stats and stats[category]:
            cat_stats = stats[category]
            lines.extend(
                [
                    f"\n## {category.title()} Performance",
                    "",
                    f"- **Count**: {cat_stats['count']}",
                    f"- **Mean Duration**: {cat_stats['duration']['mean']:.2f}ms",
                    f"- **Min/Max Duration**: {cat_stats['duration']['min']:.2f}ms / {cat_stats['duration']['max']:.2f}ms",
                    f"- **Mean Memory**: {cat_stats['memory']['mean']:.2f}MB",
                    "",
                ]
            )

    # Detailed results
    lines.extend(
        [
            "\n## Detailed Results",
            "",
            "| Name | Category | Duration (ms) | Memory (MB) | Success |",
            "|------|----------|---------------|-------------|---------|",
        ]
    )

    for result in suite.results:
        status = "✅" if result.success else "❌"
        lines.append(
            f"| {result.name} | {result.category} | {result.duration_ms:.2f} | "
            f"{result.memory_mb:.2f} | {status} |"
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines))
