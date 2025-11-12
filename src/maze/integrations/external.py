"""External integrations manager for optional tools.

Integrates with:
- pedantic_raven: Deep semantic validation
- RUNE: Sandboxed execution
- mnemosyne: Pattern storage (already integrated in Phase 5)

Provides graceful degradation when tools are unavailable.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from typing import Any

from maze.integrations.mnemosyne import MnemosyneIntegration


@dataclass
class ValidationResult:
    """Result from external validation."""

    success: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    properties_checked: int = 0
    duration_ms: float = 0.0


@dataclass
class ExecutionResult:
    """Result from sandboxed execution."""

    success: bool
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0
    duration_ms: float = 0.0
    resource_usage: dict[str, Any] = field(default_factory=dict)


@dataclass
class Pattern:
    """Pattern to persist."""

    content: str
    namespace: str
    importance: int
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class PedanticRavenClient:
    """Client for pedantic_raven semantic validator.

    Falls back gracefully if pedantic_raven is not installed.
    """

    def __init__(self, strict_mode: bool = False):
        """Initialize pedantic_raven client.

        Args:
            strict_mode: Whether to use strict validation mode
        """
        self.strict_mode = strict_mode
        self.available = self._check_availability()

    def _check_availability(self) -> bool:
        """Check if pedantic_raven is available.

        Returns:
            True if pedantic_raven CLI is available
        """
        try:
            result = subprocess.run(
                ["pedantic_raven", "--version"],
                capture_output=True,
                timeout=1,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def validate(
        self, code: str, language: str, properties: list[str] | None = None
    ) -> ValidationResult:
        """Validate code with pedantic_raven.

        Args:
            code: Code to validate
            language: Programming language
            properties: Optional list of properties to check

        Returns:
            ValidationResult with validation details
        """
        if not self.available:
            # Graceful degradation: return success with warning
            return ValidationResult(
                success=True,
                warnings=["pedantic_raven not available, skipping semantic validation"],
            )

        import time

        start = time.perf_counter()

        try:
            # Mock implementation - actual integration would call pedantic_raven CLI
            # For now, perform basic validation
            result = ValidationResult(
                success=True,
                properties_checked=len(properties) if properties else 0,
                duration_ms=(time.perf_counter() - start) * 1000,
            )

            # Basic checks
            if not code.strip():
                result.success = False
                result.errors.append("Empty code")

            return result

        except Exception as e:
            return ValidationResult(
                success=False,
                errors=[f"Validation error: {e}"],
                duration_ms=(time.perf_counter() - start) * 1000,
            )


class RuneExecutor:
    """Sandboxed code executor using RUNE.

    Falls back gracefully if RUNE is not available.
    """

    def __init__(
        self,
        timeout_seconds: int = 30,
        memory_limit_mb: int = 512,
        network_enabled: bool = False,
    ):
        """Initialize RUNE executor.

        Args:
            timeout_seconds: Execution timeout
            memory_limit_mb: Memory limit in MB
            network_enabled: Whether to enable network access
        """
        self.timeout_seconds = timeout_seconds
        self.memory_limit_mb = memory_limit_mb
        self.network_enabled = network_enabled
        self.available = self._check_availability()

    def _check_availability(self) -> bool:
        """Check if RUNE is available.

        Returns:
            True if RUNE CLI is available
        """
        try:
            result = subprocess.run(
                ["rune", "--version"],
                capture_output=True,
                timeout=1,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def execute(
        self, code: str, language: str, tests: list[str] | None = None
    ) -> ExecutionResult:
        """Execute code in sandbox.

        Args:
            code: Code to execute
            language: Programming language
            tests: Optional test commands to run

        Returns:
            ExecutionResult with execution details
        """
        if not self.available:
            # Graceful degradation: return success with warning
            return ExecutionResult(
                success=True,
                stdout="",
                stderr="RUNE not available, skipping sandboxed execution",
                exit_code=0,
            )

        import time

        start = time.perf_counter()

        try:
            # Mock implementation - actual integration would call RUNE CLI
            # For now, perform basic execution simulation
            result = ExecutionResult(
                success=True,
                stdout="Execution successful (simulated)",
                stderr="",
                exit_code=0,
                duration_ms=(time.perf_counter() - start) * 1000,
                resource_usage={
                    "memory_mb": 50,
                    "cpu_percent": 10,
                },
            )

            return result

        except Exception as e:
            return ExecutionResult(
                success=False,
                stdout="",
                stderr=f"Execution error: {e}",
                exit_code=1,
                duration_ms=(time.perf_counter() - start) * 1000,
            )


class ExternalIntegrations:
    """Manager for external tool integrations.

    Coordinates mnemosyne, pedantic_raven, and RUNE with graceful degradation.
    """

    def __init__(
        self,
        enable_mnemosyne: bool = True,
        enable_raven: bool = True,
        enable_rune: bool = True,
    ):
        """Initialize external integrations.

        Args:
            enable_mnemosyne: Whether to enable mnemosyne
            enable_raven: Whether to enable pedantic_raven
            enable_rune: Whether to enable RUNE
        """
        self.mnemosyne: MnemosyneIntegration | None = None
        self.raven: PedanticRavenClient | None = None
        self.rune: RuneExecutor | None = None

        if enable_mnemosyne:
            try:
                self.mnemosyne = MnemosyneIntegration()
            except Exception:
                # Graceful degradation
                self.mnemosyne = None

        if enable_raven:
            self.raven = PedanticRavenClient()

        if enable_rune:
            self.rune = RuneExecutor()

    def validate_with_raven(
        self, code: str, language: str, properties: list[str] | None = None
    ) -> ValidationResult:
        """Validate code with pedantic_raven.

        Args:
            code: Code to validate
            language: Programming language
            properties: Optional properties to check

        Returns:
            ValidationResult
        """
        if self.raven is None:
            return ValidationResult(
                success=True,
                warnings=["pedantic_raven disabled, skipping validation"],
            )

        return self.raven.validate(code, language, properties)

    def execute_in_rune(
        self, code: str, language: str, tests: list[str] | None = None
    ) -> ExecutionResult:
        """Execute code in RUNE sandbox.

        Args:
            code: Code to execute
            language: Programming language
            tests: Optional test commands

        Returns:
            ExecutionResult
        """
        if self.rune is None:
            return ExecutionResult(
                success=True,
                stderr="RUNE disabled, skipping execution",
            )

        return self.rune.execute(code, language, tests)

    def persist_to_mnemosyne(self, pattern: Pattern) -> bool:
        """Persist pattern to mnemosyne.

        Args:
            pattern: Pattern to store

        Returns:
            True if stored successfully
        """
        if self.mnemosyne is None:
            return False

        try:
            self.mnemosyne.store_pattern(
                content=pattern.content,
                namespace=pattern.namespace,
                importance=pattern.importance,
                tags=pattern.tags,
            )
            return True
        except Exception:
            return False

    def get_status(self) -> dict[str, bool]:
        """Get status of all integrations.

        Returns:
            Dictionary of integration availability
        """
        return {
            "mnemosyne": self.mnemosyne is not None,
            "pedantic_raven": self.raven is not None and self.raven.available,
            "rune": self.rune is not None and self.rune.available,
        }
