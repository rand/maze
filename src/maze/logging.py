"""Structured logging and metrics collection for Maze.

Provides JSON and text logging with performance metrics tracking.

Performance targets:
- Log write: <1ms
- Metrics recording: <100μs
- Metrics export: <10ms
"""

from __future__ import annotations

import json
import sys
import time
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, TextIO

from maze.config import LoggingConfig


@dataclass
class GenerationResult:
    """Result from code generation."""

    prompt: str
    code: str
    duration_ms: float
    provider: str
    model: str
    tokens_generated: int = 0
    success: bool = True
    error: Optional[str] = None


@dataclass
class ValidationResult:
    """Result from validation."""

    success: bool
    syntax_valid: bool = True
    type_valid: bool = True
    tests_passed: int = 0
    tests_failed: int = 0
    errors: List[str] = field(default_factory=list)
    duration_ms: float = 0.0


@dataclass
class RepairResult:
    """Result from repair iteration."""

    success: bool
    attempts: int
    final_code: str
    errors_fixed: List[str] = field(default_factory=list)
    duration_ms: float = 0.0


@dataclass
class PerformanceMetrics:
    """Performance metrics snapshot."""

    operation: str
    duration_ms: float
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


class StructuredLogger:
    """Structured logger with JSON and text output support."""

    def __init__(self, config: LoggingConfig):
        """Initialize structured logger.

        Args:
            config: Logging configuration
        """
        self.config = config
        self.output: TextIO

        if config.log_file is not None:
            config.log_file.parent.mkdir(parents=True, exist_ok=True)
            self.output = open(config.log_file, "a")
        else:
            self.output = sys.stdout if config.output == "stdout" else sys.stderr

    def _write_log(self, level: str, event: str, data: Dict[str, Any]) -> None:
        """Write log entry.

        Args:
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            event: Event type
            data: Event data
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "event": event,
            **data,
        }

        if self.config.format == "json":
            self.output.write(json.dumps(log_entry) + "\n")
        else:
            # Text format
            timestamp = log_entry["timestamp"]
            msg = f"[{timestamp}] {level:8} {event}: "
            if data:
                msg += " ".join(f"{k}={v}" for k, v in data.items())
            self.output.write(msg + "\n")

        self.output.flush()

    def log_generation(self, prompt: str, result: GenerationResult) -> None:
        """Log code generation event.

        Args:
            prompt: Generation prompt
            result: Generation result
        """
        self._write_log(
            "INFO" if result.success else "ERROR",
            "generation",
            {
                "prompt": prompt[:100],  # Truncate long prompts
                "duration_ms": result.duration_ms,
                "provider": result.provider,
                "model": result.model,
                "tokens": result.tokens_generated,
                "success": result.success,
                "error": result.error,
            },
        )

    def log_validation(self, validation: ValidationResult) -> None:
        """Log validation event.

        Args:
            validation: Validation result
        """
        self._write_log(
            "INFO" if validation.success else "WARNING",
            "validation",
            {
                "success": validation.success,
                "syntax_valid": validation.syntax_valid,
                "type_valid": validation.type_valid,
                "tests_passed": validation.tests_passed,
                "tests_failed": validation.tests_failed,
                "error_count": len(validation.errors),
                "duration_ms": validation.duration_ms,
            },
        )

    def log_repair(self, repair: RepairResult) -> None:
        """Log repair event.

        Args:
            repair: Repair result
        """
        self._write_log(
            "INFO" if repair.success else "ERROR",
            "repair",
            {
                "success": repair.success,
                "attempts": repair.attempts,
                "errors_fixed": len(repair.errors_fixed),
                "duration_ms": repair.duration_ms,
            },
        )

    def log_performance(self, metrics: PerformanceMetrics) -> None:
        """Log performance metrics.

        Args:
            metrics: Performance metrics
        """
        self._write_log(
            "DEBUG",
            "performance",
            {
                "operation": metrics.operation,
                "duration_ms": metrics.duration_ms,
                **metrics.metadata,
            },
        )

    def log_info(self, event: str, **kwargs: Any) -> None:
        """Log info event."""
        self._write_log("INFO", event, kwargs)

    def log_warning(self, event: str, **kwargs: Any) -> None:
        """Log warning event."""
        self._write_log("WARNING", event, kwargs)

    def log_error(self, event: str, **kwargs: Any) -> None:
        """Log error event."""
        self._write_log("ERROR", event, kwargs)

    def log_debug(self, event: str, **kwargs: Any) -> None:
        """Log debug event."""
        if self.config.level == "DEBUG":
            self._write_log("DEBUG", event, kwargs)

    def close(self) -> None:
        """Close log file if opened."""
        if self.config.log_file is not None and hasattr(self.output, "close"):
            self.output.close()


class MetricsCollector:
    """Collect and aggregate performance metrics."""

    def __init__(self):
        """Initialize metrics collector."""
        self.latencies: Dict[str, List[float]] = defaultdict(list)
        self.cache_hits: Dict[str, int] = defaultdict(int)
        self.cache_misses: Dict[str, int] = defaultdict(int)
        self.errors: Dict[str, int] = defaultdict(int)
        self.counters: Dict[str, int] = defaultdict(int)

    def record_latency(self, operation: str, duration_ms: float) -> None:
        """Record operation latency.

        Args:
            operation: Operation name
            duration_ms: Duration in milliseconds
        """
        self.latencies[operation].append(duration_ms)

    def record_cache_hit(self, cache_type: str) -> None:
        """Record cache hit.

        Args:
            cache_type: Type of cache (e.g., "grammar", "type", "pattern")
        """
        self.cache_hits[cache_type] += 1

    def record_cache_miss(self, cache_type: str) -> None:
        """Record cache miss.

        Args:
            cache_type: Type of cache
        """
        self.cache_misses[cache_type] += 1

    def record_error(self, error_type: str) -> None:
        """Record error occurrence.

        Args:
            error_type: Error type/category
        """
        self.errors[error_type] += 1

    def increment_counter(self, counter_name: str, value: int = 1) -> None:
        """Increment a counter.

        Args:
            counter_name: Counter name
            value: Value to increment by (default: 1)
        """
        self.counters[counter_name] += value

    def get_latency_stats(self, operation: str) -> Optional[Dict[str, float]]:
        """Get latency statistics for operation.

        Args:
            operation: Operation name

        Returns:
            Statistics dict with mean, min, max, p50, p95, p99 or None if no data
        """
        if operation not in self.latencies or not self.latencies[operation]:
            return None

        latencies = sorted(self.latencies[operation])
        n = len(latencies)

        return {
            "count": n,
            "mean": sum(latencies) / n,
            "min": latencies[0],
            "max": latencies[-1],
            "p50": latencies[int(n * 0.5)],
            "p95": latencies[int(n * 0.95)] if n > 1 else latencies[0],
            "p99": latencies[int(n * 0.99)] if n > 1 else latencies[0],
        }

    def get_cache_hit_rate(self, cache_type: str) -> float:
        """Get cache hit rate.

        Args:
            cache_type: Cache type

        Returns:
            Hit rate between 0.0 and 1.0
        """
        hits = self.cache_hits[cache_type]
        misses = self.cache_misses[cache_type]
        total = hits + misses

        if total == 0:
            return 0.0

        return hits / total

    def export_prometheus(self) -> str:
        """Export metrics in Prometheus format.

        Returns:
            Prometheus-formatted metrics string
        """
        lines = []

        # Latency histograms
        for operation, latencies in self.latencies.items():
            if latencies:
                stats = self.get_latency_stats(operation)
                lines.append(f"# HELP maze_latency_ms Latency for {operation}")
                lines.append(f"# TYPE maze_latency_ms summary")
                lines.append(f'maze_latency_ms{{operation="{operation}",quantile="0.5"}} {stats["p50"]}')
                lines.append(f'maze_latency_ms{{operation="{operation}",quantile="0.95"}} {stats["p95"]}')
                lines.append(f'maze_latency_ms{{operation="{operation}",quantile="0.99"}} {stats["p99"]}')
                lines.append(f'maze_latency_ms_count{{operation="{operation}"}} {stats["count"]}')
                lines.append(f'maze_latency_ms_sum{{operation="{operation}"}} {sum(latencies)}')

        # Cache metrics
        lines.append("# HELP maze_cache_hits_total Cache hits")
        lines.append("# TYPE maze_cache_hits_total counter")
        for cache_type, hits in self.cache_hits.items():
            lines.append(f'maze_cache_hits_total{{cache="{cache_type}"}} {hits}')

        lines.append("# HELP maze_cache_misses_total Cache misses")
        lines.append("# TYPE maze_cache_misses_total counter")
        for cache_type, misses in self.cache_misses.items():
            lines.append(f'maze_cache_misses_total{{cache="{cache_type}"}} {misses}')

        # Error metrics
        lines.append("# HELP maze_errors_total Errors by type")
        lines.append("# TYPE maze_errors_total counter")
        for error_type, count in self.errors.items():
            lines.append(f'maze_errors_total{{type="{error_type}"}} {count}')

        # Custom counters
        lines.append("# HELP maze_counter Custom counters")
        lines.append("# TYPE maze_counter counter")
        for counter_name, value in self.counters.items():
            lines.append(f'maze_counter{{name="{counter_name}"}} {value}')

        return "\n".join(lines) + "\n"

    def reset(self) -> None:
        """Reset all metrics."""
        self.latencies.clear()
        self.cache_hits.clear()
        self.cache_misses.clear()
        self.errors.clear()
        self.counters.clear()

    def summary(self) -> Dict[str, Any]:
        """Get summary of all metrics.

        Returns:
            Dictionary with all metrics
        """
        return {
            "latencies": {
                op: self.get_latency_stats(op) for op in self.latencies.keys()
            },
            "cache_hit_rates": {
                cache: self.get_cache_hit_rate(cache)
                for cache in set(list(self.cache_hits.keys()) + list(self.cache_misses.keys()))
            },
            "errors": dict(self.errors),
            "counters": dict(self.counters),
        }
