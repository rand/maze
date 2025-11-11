"""Tests for Maze logging and metrics system.

Test coverage target: 75%
"""

import json
import tempfile
from io import StringIO
from pathlib import Path

import pytest

from maze.config import LoggingConfig
from maze.logging import (
    GenerationResult,
    MetricsCollector,
    PerformanceMetrics,
    RepairResult,
    StructuredLogger,
    ValidationResult,
)


class TestStructuredLogger:
    """Tests for StructuredLogger."""

    def test_json_logging_to_stdout(self):
        """Test JSON logging to stdout."""
        output = StringIO()
        config = LoggingConfig(format="json", output="stdout")
        logger = StructuredLogger(config)
        logger.output = output  # Override to capture output

        logger.log_info("test_event", key="value", number=42)

        output.seek(0)
        log_line = output.read()
        data = json.loads(log_line)

        assert data["level"] == "INFO"
        assert data["event"] == "test_event"
        assert data["key"] == "value"
        assert data["number"] == 42
        assert "timestamp" in data

    def test_text_logging_format(self):
        """Test text logging format."""
        output = StringIO()
        config = LoggingConfig(format="text", output="stdout")
        logger = StructuredLogger(config)
        logger.output = output

        logger.log_info("test_event", key="value")

        output.seek(0)
        log_line = output.read()

        assert "INFO" in log_line
        assert "test_event" in log_line
        assert "key=value" in log_line

    def test_log_generation_success(self):
        """Test logging successful generation."""
        output = StringIO()
        config = LoggingConfig(format="json")
        logger = StructuredLogger(config)
        logger.output = output

        result = GenerationResult(
            prompt="test prompt",
            code="const x = 1;",
            duration_ms=100.5,
            provider="openai",
            model="gpt-4",
            tokens_generated=10,
            success=True,
        )

        logger.log_generation("test prompt", result)

        output.seek(0)
        data = json.loads(output.read())

        assert data["level"] == "INFO"
        assert data["event"] == "generation"
        assert data["success"] is True
        assert data["duration_ms"] == 100.5
        assert data["provider"] == "openai"
        assert data["tokens"] == 10

    def test_log_generation_failure(self):
        """Test logging failed generation."""
        output = StringIO()
        config = LoggingConfig(format="json")
        logger = StructuredLogger(config)
        logger.output = output

        result = GenerationResult(
            prompt="test",
            code="",
            duration_ms=50.0,
            provider="openai",
            model="gpt-4",
            success=False,
            error="API timeout",
        )

        logger.log_generation("test", result)

        output.seek(0)
        data = json.loads(output.read())

        assert data["level"] == "ERROR"
        assert data["success"] is False
        assert data["error"] == "API timeout"

    def test_log_validation(self):
        """Test logging validation results."""
        output = StringIO()
        config = LoggingConfig(format="json")
        logger = StructuredLogger(config)
        logger.output = output

        validation = ValidationResult(
            success=True,
            syntax_valid=True,
            type_valid=True,
            tests_passed=5,
            tests_failed=0,
            duration_ms=250.0,
        )

        logger.log_validation(validation)

        output.seek(0)
        data = json.loads(output.read())

        assert data["level"] == "INFO"
        assert data["event"] == "validation"
        assert data["success"] is True
        assert data["tests_passed"] == 5
        assert data["duration_ms"] == 250.0

    def test_log_validation_failure(self):
        """Test logging failed validation."""
        output = StringIO()
        config = LoggingConfig(format="json")
        logger = StructuredLogger(config)
        logger.output = output

        validation = ValidationResult(
            success=False,
            syntax_valid=False,
            errors=["Syntax error", "Type error"],
            duration_ms=100.0,
        )

        logger.log_validation(validation)

        output.seek(0)
        data = json.loads(output.read())

        assert data["level"] == "WARNING"
        assert data["success"] is False
        assert data["error_count"] == 2

    def test_log_repair(self):
        """Test logging repair results."""
        output = StringIO()
        config = LoggingConfig(format="json")
        logger = StructuredLogger(config)
        logger.output = output

        repair = RepairResult(
            success=True,
            attempts=2,
            final_code="fixed code",
            errors_fixed=["error1", "error2"],
            duration_ms=500.0,
        )

        logger.log_repair(repair)

        output.seek(0)
        data = json.loads(output.read())

        assert data["level"] == "INFO"
        assert data["event"] == "repair"
        assert data["success"] is True
        assert data["attempts"] == 2
        assert data["errors_fixed"] == 2

    def test_log_performance(self):
        """Test logging performance metrics."""
        output = StringIO()
        config = LoggingConfig(format="json")
        logger = StructuredLogger(config)
        logger.output = output

        metrics = PerformanceMetrics(
            operation="indexing",
            duration_ms=1500.0,
            metadata={"files": 100, "symbols": 5000},
        )

        logger.log_performance(metrics)

        output.seek(0)
        data = json.loads(output.read())

        assert data["level"] == "DEBUG"
        assert data["event"] == "performance"
        assert data["operation"] == "indexing"
        assert data["duration_ms"] == 1500.0
        assert data["files"] == 100

    def test_log_to_file(self):
        """Test logging to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "logs" / "maze.log"
            config = LoggingConfig(format="json", log_file=log_file)
            logger = StructuredLogger(config)

            logger.log_info("test_event", key="value")
            logger.close()

            assert log_file.exists()
            content = log_file.read_text()
            data = json.loads(content)
            assert data["event"] == "test_event"


class TestMetricsCollector:
    """Tests for MetricsCollector."""

    def test_record_latency(self):
        """Test recording latencies."""
        collector = MetricsCollector()

        collector.record_latency("indexing", 100.0)
        collector.record_latency("indexing", 150.0)
        collector.record_latency("indexing", 120.0)

        stats = collector.get_latency_stats("indexing")
        assert stats is not None
        assert stats["count"] == 3
        assert stats["min"] == 100.0
        assert stats["max"] == 150.0
        assert stats["mean"] == pytest.approx(123.33, rel=0.01)

    def test_latency_percentiles(self):
        """Test latency percentile calculations."""
        collector = MetricsCollector()

        # Record 100 samples
        for i in range(100):
            collector.record_latency("test", float(i))

        stats = collector.get_latency_stats("test")
        assert stats["p50"] == 50.0
        assert stats["p95"] == 95.0
        assert stats["p99"] == 99.0

    def test_get_latency_stats_no_data(self):
        """Test getting stats for non-existent operation."""
        collector = MetricsCollector()
        stats = collector.get_latency_stats("nonexistent")
        assert stats is None

    def test_record_cache_hit(self):
        """Test recording cache hits."""
        collector = MetricsCollector()

        collector.record_cache_hit("grammar")
        collector.record_cache_hit("grammar")
        collector.record_cache_hit("type")

        assert collector.cache_hits["grammar"] == 2
        assert collector.cache_hits["type"] == 1

    def test_record_cache_miss(self):
        """Test recording cache misses."""
        collector = MetricsCollector()

        collector.record_cache_miss("grammar")
        collector.record_cache_miss("pattern")

        assert collector.cache_misses["grammar"] == 1
        assert collector.cache_misses["pattern"] == 1

    def test_cache_hit_rate(self):
        """Test cache hit rate calculation."""
        collector = MetricsCollector()

        collector.record_cache_hit("grammar")
        collector.record_cache_hit("grammar")
        collector.record_cache_hit("grammar")
        collector.record_cache_miss("grammar")

        hit_rate = collector.get_cache_hit_rate("grammar")
        assert hit_rate == 0.75

    def test_cache_hit_rate_no_data(self):
        """Test cache hit rate with no data."""
        collector = MetricsCollector()
        hit_rate = collector.get_cache_hit_rate("nonexistent")
        assert hit_rate == 0.0

    def test_record_error(self):
        """Test recording errors."""
        collector = MetricsCollector()

        collector.record_error("timeout")
        collector.record_error("timeout")
        collector.record_error("syntax_error")

        assert collector.errors["timeout"] == 2
        assert collector.errors["syntax_error"] == 1

    def test_increment_counter(self):
        """Test incrementing counters."""
        collector = MetricsCollector()

        collector.increment_counter("generations")
        collector.increment_counter("generations")
        collector.increment_counter("validations", 5)

        assert collector.counters["generations"] == 2
        assert collector.counters["validations"] == 5

    def test_export_prometheus(self):
        """Test Prometheus export format."""
        collector = MetricsCollector()

        collector.record_latency("indexing", 100.0)
        collector.record_latency("indexing", 200.0)
        collector.record_cache_hit("grammar")
        collector.record_cache_miss("grammar")
        collector.record_error("timeout")
        collector.increment_counter("generations", 10)

        prometheus_output = collector.export_prometheus()

        assert "maze_latency_ms" in prometheus_output
        assert 'operation="indexing"' in prometheus_output
        assert "maze_cache_hits_total" in prometheus_output
        assert "maze_cache_misses_total" in prometheus_output
        assert "maze_errors_total" in prometheus_output
        assert "maze_counter" in prometheus_output

    def test_reset_metrics(self):
        """Test resetting all metrics."""
        collector = MetricsCollector()

        collector.record_latency("test", 100.0)
        collector.record_cache_hit("grammar")
        collector.record_error("timeout")
        collector.increment_counter("test")

        collector.reset()

        assert len(collector.latencies) == 0
        assert len(collector.cache_hits) == 0
        assert len(collector.cache_misses) == 0
        assert len(collector.errors) == 0
        assert len(collector.counters) == 0

    def test_summary(self):
        """Test metrics summary."""
        collector = MetricsCollector()

        collector.record_latency("indexing", 100.0)
        collector.record_latency("indexing", 200.0)
        collector.record_cache_hit("grammar")
        collector.record_cache_miss("grammar")
        collector.record_error("timeout")
        collector.increment_counter("generations", 5)

        summary = collector.summary()

        assert "latencies" in summary
        assert "indexing" in summary["latencies"]
        assert summary["latencies"]["indexing"]["count"] == 2

        assert "cache_hit_rates" in summary
        assert summary["cache_hit_rates"]["grammar"] == 0.5

        assert "errors" in summary
        assert summary["errors"]["timeout"] == 1

        assert "counters" in summary
        assert summary["counters"]["generations"] == 5


class TestLoggingIntegration:
    """Integration tests for logging and metrics."""

    def test_logger_with_metrics(self):
        """Test using logger and metrics together."""
        output = StringIO()
        config = LoggingConfig(format="json")
        logger = StructuredLogger(config)
        logger.output = output

        collector = MetricsCollector()

        # Simulate generation workflow
        import time

        start = time.perf_counter()
        result = GenerationResult(
            prompt="test",
            code="const x = 1;",
            duration_ms=100.0,
            provider="openai",
            model="gpt-4",
            success=True,
        )
        duration_ms = (time.perf_counter() - start) * 1000

        logger.log_generation("test", result)
        collector.record_latency("generation", duration_ms)
        collector.increment_counter("successful_generations")

        # Verify both systems recorded the event
        output.seek(0)
        log_data = json.loads(output.read())
        assert log_data["event"] == "generation"

        stats = collector.get_latency_stats("generation")
        assert stats is not None
        assert collector.counters["successful_generations"] == 1
