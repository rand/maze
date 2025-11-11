"""Tests for benchmark framework.

Test coverage target: 75%
"""

import tempfile
from pathlib import Path

import pytest

from maze.benchmarking import (
    BenchmarkResult,
    BenchmarkRunner,
    BenchmarkSuite,
    generate_report,
)
from maze.config import Config


class TestBenchmarkResult:
    """Tests for BenchmarkResult."""

    def test_default_values(self):
        """Test default benchmark result."""
        result = BenchmarkResult(
            name="test",
            category="indexing",
            duration_ms=100.0,
            memory_mb=50.0,
        )

        assert result.name == "test"
        assert result.category == "indexing"
        assert result.success is True
        assert result.error is None

    def test_with_metrics(self):
        """Test result with metrics."""
        result = BenchmarkResult(
            name="test",
            category="generation",
            duration_ms=500.0,
            memory_mb=100.0,
            metrics={"tokens": 100, "cache_hits": 5},
        )

        assert result.metrics["tokens"] == 100
        assert result.metrics["cache_hits"] == 5

    def test_failed_result(self):
        """Test failed benchmark result."""
        result = BenchmarkResult(
            name="test",
            category="stress",
            duration_ms=1000.0,
            memory_mb=200.0,
            success=False,
            error="Timeout",
        )

        assert result.success is False
        assert result.error == "Timeout"


class TestBenchmarkSuite:
    """Tests for BenchmarkSuite."""

    def test_initialization(self):
        """Test suite initialization."""
        suite = BenchmarkSuite(name="Test Suite")

        assert suite.name == "Test Suite"
        assert len(suite.results) == 0
        assert suite.timestamp is not None

    def test_add_result(self):
        """Test adding results to suite."""
        suite = BenchmarkSuite(name="Test")

        result1 = BenchmarkResult("test1", "indexing", 100.0, 50.0)
        result2 = BenchmarkResult("test2", "generation", 200.0, 75.0)

        suite.add_result(result1)
        suite.add_result(result2)

        assert len(suite.results) == 2

    def test_get_statistics_all(self):
        """Test getting statistics for all results."""
        suite = BenchmarkSuite(name="Test")

        suite.add_result(BenchmarkResult("test1", "indexing", 100.0, 50.0))
        suite.add_result(BenchmarkResult("test2", "indexing", 200.0, 75.0))
        suite.add_result(BenchmarkResult("test3", "indexing", 150.0, 60.0))

        stats = suite.get_statistics()

        assert stats["count"] == 3
        assert stats["duration"]["mean"] == pytest.approx(150.0)
        assert stats["duration"]["median"] == 150.0
        assert stats["memory"]["mean"] == pytest.approx(61.67, rel=0.01)

    def test_get_statistics_by_category(self):
        """Test getting statistics filtered by category."""
        suite = BenchmarkSuite(name="Test")

        suite.add_result(BenchmarkResult("test1", "indexing", 100.0, 50.0))
        suite.add_result(BenchmarkResult("test2", "generation", 200.0, 75.0))
        suite.add_result(BenchmarkResult("test3", "indexing", 150.0, 60.0))

        stats = suite.get_statistics("indexing")

        assert stats["count"] == 2
        assert stats["duration"]["mean"] == 125.0

    def test_get_statistics_empty(self):
        """Test statistics for empty suite."""
        suite = BenchmarkSuite(name="Empty")

        stats = suite.get_statistics()

        assert stats == {}

    def test_to_dict(self):
        """Test converting suite to dictionary."""
        suite = BenchmarkSuite(name="Test")
        suite.add_result(BenchmarkResult("test1", "indexing", 100.0, 50.0))

        data = suite.to_dict()

        assert data["name"] == "Test"
        assert "timestamp" in data
        assert len(data["results"]) == 1
        assert "statistics" in data

    def test_save_to_file(self):
        """Test saving suite to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "results" / "bench.json"

            suite = BenchmarkSuite(name="Test")
            suite.add_result(BenchmarkResult("test", "indexing", 100.0, 50.0))

            suite.save(output_path)

            assert output_path.exists()


class TestBenchmarkRunner:
    """Tests for BenchmarkRunner."""

    def test_initialization(self):
        """Test runner initialization."""
        runner = BenchmarkRunner()

        assert runner.config is not None
        assert runner.pipeline is not None

    def test_benchmark_indexing(self):
        """Test indexing benchmark."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            ts_file = project_path / "test.ts"
            ts_file.write_text("const x = 1;")

            config = Config()
            config.project.language = "typescript"
            runner = BenchmarkRunner(config)

            result = runner.benchmark_indexing(project_path, "Test Indexing")

            assert result.name == "Test Indexing"
            assert result.category == "indexing"
            assert result.duration_ms > 0
            assert result.success is True
            assert result.metrics["files"] > 0

    def test_benchmark_generation(self):
        """Test generation benchmark."""
        config = Config()
        config.project.language = "typescript"
        runner = BenchmarkRunner(config)

        result = runner.benchmark_generation(
            "Create a function", "Test Generation", iterations=2
        )

        assert result.name == "Test Generation"
        assert result.category == "generation"
        assert result.duration_ms > 0
        assert result.metrics["iterations"] == 2

    def test_benchmark_validation(self):
        """Test validation benchmark."""
        config = Config()
        config.project.language = "typescript"
        runner = BenchmarkRunner(config)

        result = runner.benchmark_validation(
            "const x: number = 42;", "Test Validation", iterations=5
        )

        assert result.name == "Test Validation"
        assert result.category == "validation"
        assert result.metrics["iterations"] == 5
        assert "throughput" in result.metrics

    def test_stress_test_concurrent(self):
        """Test concurrent stress test."""
        config = Config()
        config.project.language = "typescript"
        runner = BenchmarkRunner(config)

        prompts = ["test1", "test2", "test3"]
        result = runner.stress_test_concurrent(prompts, "Stress Test")

        assert result.category == "stress"
        assert result.metrics["prompts"] == 3

    def test_profile_memory(self):
        """Test memory profiling."""
        config = Config()
        config.project.language = "typescript"
        runner = BenchmarkRunner(config)

        operations = ["generate", "validate"]
        result = runner.profile_memory(operations, "Memory Test")

        assert result.category == "stress"
        assert result.metrics["operations"] == 2
        assert "peak_memory" in result.metrics


class TestReportGeneration:
    """Tests for report generation."""

    def test_generate_report(self):
        """Test generating markdown report."""
        with tempfile.TemporaryDirectory() as tmpdir:
            report_path = Path(tmpdir) / "report.md"

            suite = BenchmarkSuite(name="Test Suite")
            suite.add_result(BenchmarkResult("bench1", "indexing", 100.0, 50.0))
            suite.add_result(BenchmarkResult("bench2", "generation", 200.0, 75.0))

            generate_report(suite, report_path)

            assert report_path.exists()
            content = report_path.read_text()
            assert "Test Suite" in content
            assert "bench1" in content
            assert "indexing" in content
