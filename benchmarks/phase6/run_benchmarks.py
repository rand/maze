"""Main benchmark runner for Phase 6 performance validation.

Runs comprehensive benchmarks covering:
- Small project indexing (1K-5K LOC)
- Medium project indexing (10K-50K LOC)
- Large project indexing (100K+ LOC)
- Generation performance
- Validation throughput
- Stress testing scenarios

Usage:
    python benchmarks/phase6/run_benchmarks.py
    python benchmarks/phase6/run_benchmarks.py --category indexing
    python benchmarks/phase6/run_benchmarks.py --output results.json
"""

import argparse
import sys
import tempfile
from pathlib import Path

from maze.benchmarking import BenchmarkRunner, BenchmarkSuite, generate_report
from maze.config import Config


def create_synthetic_project(size: str) -> Path:
    """Create synthetic TypeScript project for benchmarking.

    Args:
        size: Project size (small, medium, large)

    Returns:
        Path to created project
    """
    tmpdir = tempfile.mkdtemp()
    project = Path(tmpdir)

    # File counts for different sizes
    sizes = {
        "small": 10,      # ~1K LOC
        "medium": 100,    # ~10K LOC
        "large": 1000,    # ~100K LOC
    }

    file_count = sizes.get(size, 10)
    
    for i in range(file_count):
        file_path = project / f"file{i:04d}.ts"
        
        # Generate ~100 LOC per file
        code_lines = []
        code_lines.append(f"// File {i}")
        code_lines.append("")
        
        for j in range(10):
            code_lines.append(f"export function func{i}_{j}(x: number): number {{")
            code_lines.append(f"    const y = x * {j + 1};")
            code_lines.append(f"    return y + {i};")
            code_lines.append("}")
            code_lines.append("")

        file_path.write_text("\n".join(code_lines))

    return project


def run_indexing_benchmarks(runner: BenchmarkRunner, suite: BenchmarkSuite) -> None:
    """Run indexing benchmarks.

    Args:
        runner: Benchmark runner
        suite: Suite to add results to
    """
    print("Running indexing benchmarks...")

    # Small project
    print("  - Small project (1K-5K LOC)...")
    small_project = create_synthetic_project("small")
    result = runner.benchmark_indexing(small_project, "Small Project Indexing")
    suite.add_result(result)
    print(f"    Duration: {result.duration_ms:.0f}ms, Memory: {result.memory_mb:.0f}MB")

    # Medium project
    print("  - Medium project (10K-50K LOC)...")
    medium_project = create_synthetic_project("medium")
    result = runner.benchmark_indexing(medium_project, "Medium Project Indexing")
    suite.add_result(result)
    print(f"    Duration: {result.duration_ms:.0f}ms, Memory: {result.memory_mb:.0f}MB")

    # Large project
    print("  - Large project (100K+ LOC)...")
    large_project = create_synthetic_project("large")
    result = runner.benchmark_indexing(large_project, "Large Project Indexing")
    suite.add_result(result)
    print(f"    Duration: {result.duration_ms:.0f}ms, Memory: {result.memory_mb:.0f}MB")

    # Validate target: <30s for 100K LOC
    if result.duration_ms < 30000:
        print(f"    ✅ Met target (<30s)")
    else:
        print(f"    ⚠️  Exceeded target: {result.duration_ms/1000:.1f}s > 30s")


def run_generation_benchmarks(runner: BenchmarkRunner, suite: BenchmarkSuite) -> None:
    """Run generation benchmarks.

    Args:
        runner: Benchmark runner
        suite: Suite to add results to
    """
    print("\nRunning generation benchmarks...")

    prompts = [
        "Create a function that adds two numbers",
        "Create a TypeScript class with getter and setter",
        "Create an async function with error handling",
        "Create an interface with generic types",
        "Create a function with complex return type",
    ]

    for i, prompt in enumerate(prompts, 1):
        print(f"  - Prompt {i}/5...")
        result = runner.benchmark_generation(
            prompt, f"Generation: {prompt[:40]}...", iterations=3
        )
        suite.add_result(result)
        print(f"    Duration: {result.duration_ms:.0f}ms")

    # Check target: <10s per prompt
    avg_duration = suite.get_statistics("generation")["duration"]["mean"]
    if avg_duration < 10000:
        print(f"  ✅ Met target (<10s average)")
    else:
        print(f"  ⚠️  Exceeded target: {avg_duration/1000:.1f}s > 10s")


def run_validation_benchmarks(runner: BenchmarkRunner, suite: BenchmarkSuite) -> None:
    """Run validation benchmarks.

    Args:
        runner: Benchmark runner
        suite: Suite to add results to
    """
    print("\nRunning validation benchmarks...")

    test_codes = [
        "const x: number = 42;",
        "function add(a: number, b: number): number { return a + b; }",
        "class Calculator { add(a: number, b: number) { return a + b; } }",
    ]

    for i, code in enumerate(test_codes, 1):
        print(f"  - Test case {i}/3...")
        result = runner.benchmark_validation(code, f"Validation: Test {i}", iterations=10)
        suite.add_result(result)
        print(f"    Throughput: {result.metrics['throughput']:.0f} ops/sec")


def run_stress_tests(runner: BenchmarkRunner, suite: BenchmarkSuite) -> None:
    """Run stress tests.

    Args:
        runner: Benchmark runner
        suite: Suite to add results to
    """
    print("\nRunning stress tests...")

    # Concurrent generations
    print("  - Concurrent generations (10 prompts)...")
    prompts = [f"Create function {i}" for i in range(10)]
    result = runner.stress_test_concurrent(prompts, "Concurrent 10x")
    suite.add_result(result)
    print(f"    Duration: {result.duration_ms:.0f}ms, Avg: {result.metrics['avg_per_prompt']:.0f}ms/prompt")

    # Memory profiling
    print("  - Memory profiling...")
    operations = ["index", "generate", "validate"] * 10
    result = runner.profile_memory(operations, "Memory Profile 30 ops")
    suite.add_result(result)
    print(f"    Peak Memory: {result.metrics['peak_memory']:.0f}MB")

    # Validate target: <2GB memory
    if result.metrics['peak_memory'] < 2048:
        print(f"  ✅ Met target (<2GB)")
    else:
        print(f"  ⚠️  Exceeded target: {result.metrics['peak_memory']:.0f}MB > 2GB")


def main() -> int:
    """Main benchmark runner.

    Returns:
        Exit code
    """
    parser = argparse.ArgumentParser(description="Run Phase 6 performance benchmarks")
    parser.add_argument(
        "--category",
        choices=["indexing", "generation", "validation", "stress", "all"],
        default="all",
        help="Benchmark category to run",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("benchmarks/phase6/results.json"),
        help="Output path for results",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("benchmarks/phase6/REPORT.md"),
        help="Output path for markdown report",
    )

    args = parser.parse_args()

    print("=" * 70)
    print("Phase 6 Performance Benchmarks")
    print("=" * 70)

    config = Config()
    config.project.language = "typescript"
    
    runner = BenchmarkRunner(config)
    suite = BenchmarkSuite(name="Phase 6 Performance Validation")

    # Run benchmarks
    if args.category in ["indexing", "all"]:
        run_indexing_benchmarks(runner, suite)

    if args.category in ["generation", "all"]:
        run_generation_benchmarks(runner, suite)

    if args.category in ["validation", "all"]:
        run_validation_benchmarks(runner, suite)

    if args.category in ["stress", "all"]:
        run_stress_tests(runner, suite)

    # Save results
    print(f"\n{'=' * 70}")
    print(f"Saving results to {args.output}...")
    suite.save(args.output)

    print(f"Generating report to {args.report}...")
    generate_report(suite, args.report)

    # Print summary
    print(f"\n{'=' * 70}")
    print("Summary:")
    stats = suite.get_statistics()
    print(f"  Total benchmarks: {stats['count']}")
    print(f"  Success rate: {stats['success_rate']:.1%}")
    print(f"  Avg duration: {stats['duration']['mean']:.2f}ms")
    print(f"  Avg memory: {stats['memory']['mean']:.2f}MB")

    print(f"\n✅ Benchmarks complete!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
