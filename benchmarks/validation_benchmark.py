#!/usr/bin/env python3
"""
Performance benchmarks for Phase 4 validation system.

Measures actual performance against targets:
- Syntax validation: <50ms
- Type validation: <200ms
- Lint validation: <100ms
- Full pipeline (no tests): <500ms
- Repair iteration: <2s
"""

import time
import statistics
from typing import Callable

from maze.validation.pipeline import ValidationPipeline, ValidationContext, TypeContext
from maze.validation.syntax import SyntaxValidator
from maze.validation.types import TypeValidator
from maze.validation.lint import LintValidator, LintRules
from maze.repair.orchestrator import RepairOrchestrator


def benchmark(name: str, func: Callable, iterations: int = 10) -> dict:
    """Run benchmark and return statistics."""
    times = []

    # Warmup
    for _ in range(2):
        func()

    # Actual benchmark
    for _ in range(iterations):
        start = time.perf_counter()
        func()
        elapsed = (time.perf_counter() - start) * 1000
        times.append(elapsed)

    return {
        "name": name,
        "min": min(times),
        "max": max(times),
        "mean": statistics.mean(times),
        "median": statistics.median(times),
        "stdev": statistics.stdev(times) if len(times) > 1 else 0,
        "iterations": iterations,
    }


def run_benchmarks():
    """Run all benchmarks."""
    print("=" * 70)
    print("Phase 4 Validation System - Performance Benchmarks")
    print("=" * 70)
    print()

    # Test code samples
    simple_code = "def foo(): return 42"

    medium_code = '''
def calculate(x: int, y: int) -> int:
    """Calculate result."""
    if x > 0:
        return x + y
    else:
        return x - y
'''

    large_functions = []
    for i in range(20):
        large_functions.extend([
            f"def function_{i}(x):",
            f"    return x * {i}",
            ""
        ])
    large_code = "\n".join(large_functions)

    # Benchmark 1: Syntax validation
    print("1. Syntax Validation")
    print("-" * 70)

    syntax_validator = SyntaxValidator()

    simple_syntax = benchmark(
        "Simple code (1 line)",
        lambda: syntax_validator.validate(simple_code, "python"),
        iterations=50
    )

    medium_syntax = benchmark(
        "Medium code (~10 lines)",
        lambda: syntax_validator.validate(medium_code, "python"),
        iterations=50
    )

    large_syntax = benchmark(
        "Large code (~60 lines)",
        lambda: syntax_validator.validate(large_code, "python"),
        iterations=20
    )

    print(f"  Simple:  {simple_syntax['mean']:.2f}ms ± {simple_syntax['stdev']:.2f}ms")
    print(f"  Medium:  {medium_syntax['mean']:.2f}ms ± {medium_syntax['stdev']:.2f}ms")
    print(f"  Large:   {large_syntax['mean']:.2f}ms ± {large_syntax['stdev']:.2f}ms")
    print(f"  Target:  <50ms")
    print(f"  Status:  {'✓ PASS' if large_syntax['mean'] < 50 else '✗ FAIL'}")
    print()

    # Benchmark 2: Type validation
    print("2. Type Validation")
    print("-" * 70)

    type_validator = TypeValidator()
    type_context = TypeContext()

    type_bench = benchmark(
        "Type checking",
        lambda: type_validator.validate(medium_code, "python", type_context),
        iterations=20
    )

    print(f"  Mean:    {type_bench['mean']:.2f}ms ± {type_bench['stdev']:.2f}ms")
    print(f"  Target:  <200ms")
    print(f"  Status:  {'✓ PASS' if type_bench['mean'] < 200 else '✗ FAIL'}")
    print()

    # Benchmark 3: Lint validation
    print("3. Lint Validation")
    print("-" * 70)

    lint_validator = LintValidator(rules=LintRules.default())

    lint_bench = benchmark(
        "Lint checking",
        lambda: lint_validator.validate(medium_code, "python"),
        iterations=20
    )

    print(f"  Mean:    {lint_bench['mean']:.2f}ms ± {lint_bench['stdev']:.2f}ms")
    print(f"  Target:  <100ms")
    print(f"  Status:  {'✓ PASS' if lint_bench['mean'] < 100 else '✗ FAIL'}")
    print()

    # Benchmark 4: Full pipeline (no tests)
    print("4. Full Validation Pipeline (syntax + types + lint)")
    print("-" * 70)

    pipeline = ValidationPipeline()
    context = ValidationContext(
        type_context=TypeContext(),
        lint_rules=LintRules.default(),
    )

    pipeline_bench = benchmark(
        "Full pipeline",
        lambda: pipeline.validate(
            medium_code, "python", context, stages=["syntax", "types", "lint"]
        ),
        iterations=10
    )

    print(f"  Mean:    {pipeline_bench['mean']:.2f}ms ± {pipeline_bench['stdev']:.2f}ms")
    print(f"  Target:  <500ms")
    print(f"  Status:  {'✓ PASS' if pipeline_bench['mean'] < 500 else '✗ FAIL'}")
    print()

    # Benchmark 5: Parallel vs Sequential
    print("5. Parallel vs Sequential Validation")
    print("-" * 70)

    pipeline_parallel = ValidationPipeline(parallel_validation=True)
    pipeline_sequential = ValidationPipeline(parallel_validation=False)

    parallel_bench = benchmark(
        "Parallel (syntax + lint)",
        lambda: pipeline_parallel.validate(
            medium_code, "python", context, stages=["syntax", "lint"]
        ),
        iterations=20
    )

    sequential_bench = benchmark(
        "Sequential (syntax + lint)",
        lambda: pipeline_sequential.validate(
            medium_code, "python", context, stages=["syntax", "lint"]
        ),
        iterations=20
    )

    speedup = sequential_bench['mean'] / parallel_bench['mean'] if parallel_bench['mean'] > 0 else 1.0

    print(f"  Parallel:    {parallel_bench['mean']:.2f}ms ± {parallel_bench['stdev']:.2f}ms")
    print(f"  Sequential:  {sequential_bench['mean']:.2f}ms ± {sequential_bench['stdev']:.2f}ms")
    print(f"  Speedup:     {speedup:.2f}x")
    print()

    # Benchmark 6: Repair iteration
    print("6. Repair Orchestrator")
    print("-" * 70)

    orchestrator = RepairOrchestrator(validator=pipeline, max_attempts=1)

    repair_bench = benchmark(
        "Repair iteration (1 attempt)",
        lambda: orchestrator.repair(
            code=simple_code,
            prompt="Create function",
            grammar="",
            language="python",
            max_attempts=1
        ),
        iterations=10
    )

    print(f"  Mean:    {repair_bench['mean']:.2f}ms ± {repair_bench['stdev']:.2f}ms")
    print(f"  Target:  <2000ms")
    print(f"  Status:  {'✓ PASS' if repair_bench['mean'] < 2000 else '✗ FAIL'}")
    print()

    # Benchmark 7: Caching effectiveness
    print("7. Cache Performance")
    print("-" * 70)

    # First run (cold cache)
    start = time.perf_counter()
    pipeline.validate(simple_code, "python", stages=["syntax"])
    cold_time = (time.perf_counter() - start) * 1000

    # Second run (warm cache)
    start = time.perf_counter()
    pipeline.validate(simple_code, "python", stages=["syntax"])
    warm_time = (time.perf_counter() - start) * 1000

    cache_speedup = cold_time / warm_time if warm_time > 0 else 1.0

    print(f"  Cold cache:  {cold_time:.2f}ms")
    print(f"  Warm cache:  {warm_time:.2f}ms")
    print(f"  Speedup:     {cache_speedup:.2f}x")
    print()

    # Summary
    print("=" * 70)
    print("Summary")
    print("=" * 70)

    all_pass = (
        large_syntax['mean'] < 50
        and type_bench['mean'] < 200
        and lint_bench['mean'] < 100
        and pipeline_bench['mean'] < 500
        and repair_bench['mean'] < 2000
    )

    print(f"Overall: {'✓ ALL TARGETS MET' if all_pass else '✗ SOME TARGETS MISSED'}")
    print()

    # Statistics
    stats = pipeline.get_pipeline_stats()
    print("Pipeline Statistics:")
    print(f"  Total validations: {stats['total_validations']}")
    print(f"  Average time: {stats['average_validation_time_ms']:.2f}ms")
    print(f"  Success rate: {stats['success_rate']:.1%}")
    print()

    repair_stats = orchestrator.get_repair_stats()
    print("Repair Statistics:")
    print(f"  Total repairs: {repair_stats['total_repairs']}")
    print(f"  Success rate: {repair_stats['success_rate']:.1%}")
    print(f"  Average attempts: {repair_stats['avg_attempts']:.2f}")
    print()


if __name__ == "__main__":
    run_benchmarks()
