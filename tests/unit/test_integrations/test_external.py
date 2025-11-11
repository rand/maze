"""Tests for external integrations manager.

Test coverage target: 70%
"""

from unittest.mock import Mock, patch

import pytest

from maze.integrations.external import (
    ExternalIntegrations,
    ExecutionResult,
    Pattern,
    PedanticRavenClient,
    RuneExecutor,
    ValidationResult,
)


class TestPedanticRavenClient:
    """Tests for PedanticRavenClient."""

    def test_initialization(self):
        """Test client initialization."""
        client = PedanticRavenClient(strict_mode=True)
        assert client.strict_mode is True
        assert isinstance(client.available, bool)

    def test_availability_check_not_installed(self):
        """Test availability check when not installed."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError()
            client = PedanticRavenClient()
            assert client.available is False

    def test_availability_check_installed(self):
        """Test availability check when installed."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0)
            client = PedanticRavenClient()
            assert client.available is True

    def test_validate_when_unavailable(self):
        """Test validation when pedantic_raven is unavailable."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError()
            client = PedanticRavenClient()

            result = client.validate("const x = 1;", "typescript")

            assert isinstance(result, ValidationResult)
            assert result.success is True
            assert len(result.warnings) > 0
            assert "not available" in result.warnings[0]

    def test_validate_when_available(self):
        """Test validation when pedantic_raven is available."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0)
            client = PedanticRavenClient()

            result = client.validate("const x = 1;", "typescript", ["type_safety"])

            assert isinstance(result, ValidationResult)
            assert result.success is True

    def test_validate_empty_code(self):
        """Test validation with empty code."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0)
            client = PedanticRavenClient()

            result = client.validate("", "typescript")

            assert result.success is False
            assert any("Empty" in err for err in result.errors)

    def test_validate_with_properties(self):
        """Test validation with specific properties."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0)
            client = PedanticRavenClient()

            properties = ["null_safety", "type_safety", "memory_safety"]
            result = client.validate("code", "rust", properties)

            assert result.properties_checked == 3


class TestRuneExecutor:
    """Tests for RuneExecutor."""

    def test_initialization(self):
        """Test executor initialization."""
        executor = RuneExecutor(
            timeout_seconds=60, memory_limit_mb=1024, network_enabled=True
        )
        assert executor.timeout_seconds == 60
        assert executor.memory_limit_mb == 1024
        assert executor.network_enabled is True

    def test_availability_check_not_installed(self):
        """Test availability check when not installed."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError()
            executor = RuneExecutor()
            assert executor.available is False

    def test_availability_check_installed(self):
        """Test availability check when installed."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0)
            executor = RuneExecutor()
            assert executor.available is True

    def test_execute_when_unavailable(self):
        """Test execution when RUNE is unavailable."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError()
            executor = RuneExecutor()

            result = executor.execute("console.log('test');", "javascript")

            assert isinstance(result, ExecutionResult)
            assert result.success is True
            assert "not available" in result.stderr

    def test_execute_when_available(self):
        """Test execution when RUNE is available."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0)
            executor = RuneExecutor()

            result = executor.execute("console.log('test');", "javascript")

            assert isinstance(result, ExecutionResult)
            assert result.success is True
            assert result.exit_code == 0

    def test_execute_with_tests(self):
        """Test execution with test commands."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0)
            executor = RuneExecutor()

            tests = ["npm test", "npm run coverage"]
            result = executor.execute("code", "javascript", tests)

            assert result.success is True

    def test_execute_resource_usage(self):
        """Test execution tracks resource usage."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0)
            executor = RuneExecutor()

            result = executor.execute("code", "python")

            assert "resource_usage" in result.__dict__
            assert isinstance(result.resource_usage, dict)


class TestExternalIntegrations:
    """Tests for ExternalIntegrations manager."""

    def test_initialization_default(self):
        """Test initialization with defaults."""
        integrations = ExternalIntegrations()
        
        # Check components were created
        assert integrations.raven is not None
        assert integrations.rune is not None

    def test_initialization_selective(self):
        """Test selective initialization."""
        integrations = ExternalIntegrations(
            enable_mnemosyne=False,
            enable_raven=True,
            enable_rune=False,
        )

        assert integrations.mnemosyne is None
        assert integrations.raven is not None
        assert integrations.rune is None

    def test_validate_with_raven_enabled(self):
        """Test validation with raven enabled."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0)
            integrations = ExternalIntegrations()

            result = integrations.validate_with_raven("code", "python")

            assert isinstance(result, ValidationResult)

    def test_validate_with_raven_disabled(self):
        """Test validation with raven disabled."""
        integrations = ExternalIntegrations(enable_raven=False)

        result = integrations.validate_with_raven("code", "python")

        assert result.success is True
        assert len(result.warnings) > 0

    def test_execute_in_rune_enabled(self):
        """Test execution with RUNE enabled."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0)
            integrations = ExternalIntegrations()

            result = integrations.execute_in_rune("code", "python")

            assert isinstance(result, ExecutionResult)

    def test_execute_in_rune_disabled(self):
        """Test execution with RUNE disabled."""
        integrations = ExternalIntegrations(enable_rune=False)

        result = integrations.execute_in_rune("code", "python")

        assert result.success is True
        assert "disabled" in result.stderr

    def test_persist_to_mnemosyne_enabled(self):
        """Test persistence with mnemosyne enabled."""
        integrations = ExternalIntegrations(enable_mnemosyne=True)

        pattern = Pattern(
            content="test pattern",
            namespace="test",
            importance=5,
            tags=["test"],
        )

        # May succeed or fail depending on mnemosyne availability
        result = integrations.persist_to_mnemosyne(pattern)
        assert isinstance(result, bool)

    def test_persist_to_mnemosyne_disabled(self):
        """Test persistence with mnemosyne disabled."""
        integrations = ExternalIntegrations(enable_mnemosyne=False)

        pattern = Pattern(
            content="test pattern",
            namespace="test",
            importance=5,
        )

        result = integrations.persist_to_mnemosyne(pattern)
        assert result is False

    def test_get_status(self):
        """Test getting integration status."""
        integrations = ExternalIntegrations()

        status = integrations.get_status()

        assert isinstance(status, dict)
        assert "mnemosyne" in status
        assert "pedantic_raven" in status
        assert "rune" in status
        assert all(isinstance(v, bool) for v in status.values())

    def test_graceful_degradation_all_disabled(self):
        """Test graceful degradation with all tools disabled."""
        integrations = ExternalIntegrations(
            enable_mnemosyne=False,
            enable_raven=False,
            enable_rune=False,
        )

        # All operations should still work
        val_result = integrations.validate_with_raven("code", "python")
        exec_result = integrations.execute_in_rune("code", "python")
        pattern = Pattern("test", "ns", 5)
        persist_result = integrations.persist_to_mnemosyne(pattern)

        assert val_result.success is True
        assert exec_result.success is True
        assert persist_result is False


class TestValidationResult:
    """Tests for ValidationResult dataclass."""

    def test_default_values(self):
        """Test default values."""
        result = ValidationResult(success=True)
        assert result.success is True
        assert result.errors == []
        assert result.warnings == []
        assert result.properties_checked == 0

    def test_with_errors(self):
        """Test result with errors."""
        result = ValidationResult(
            success=False, errors=["Error 1", "Error 2"], warnings=["Warning 1"]
        )
        assert result.success is False
        assert len(result.errors) == 2
        assert len(result.warnings) == 1


class TestExecutionResult:
    """Tests for ExecutionResult dataclass."""

    def test_default_values(self):
        """Test default values."""
        result = ExecutionResult(success=True)
        assert result.success is True
        assert result.stdout == ""
        assert result.stderr == ""
        assert result.exit_code == 0

    def test_with_output(self):
        """Test result with output."""
        result = ExecutionResult(
            success=True,
            stdout="Output here",
            stderr="",
            exit_code=0,
            duration_ms=100.5,
        )
        assert result.stdout == "Output here"
        assert result.duration_ms == 100.5


class TestPattern:
    """Tests for Pattern dataclass."""

    def test_default_values(self):
        """Test default values."""
        pattern = Pattern(content="test", namespace="ns", importance=5)
        assert pattern.content == "test"
        assert pattern.namespace == "ns"
        assert pattern.importance == 5
        assert pattern.tags == []
        assert pattern.metadata == {}

    def test_with_tags_and_metadata(self):
        """Test with tags and metadata."""
        pattern = Pattern(
            content="pattern",
            namespace="test",
            importance=7,
            tags=["tag1", "tag2"],
            metadata={"key": "value"},
        )
        assert len(pattern.tags) == 2
        assert pattern.metadata["key"] == "value"
