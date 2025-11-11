"""Tests for examples - ensure all examples run without errors.

Test coverage: 100% (all examples must run)
"""

import subprocess
import sys
from pathlib import Path

import pytest


EXAMPLES_DIR = Path(__file__).parent.parent.parent.parent / "examples"


class TestBasicExamples:
    """Tests for basic TypeScript examples."""

    def test_01_function_generation(self):
        """Test function generation example runs."""
        example = EXAMPLES_DIR / "typescript" / "01-function-generation.py"
        assert example.exists()

        result = subprocess.run(
            [sys.executable, str(example)],
            capture_output=True,
            timeout=30,
        )

        assert result.returncode == 0
        assert b"Example complete" in result.stdout

    def test_02_class_generation(self):
        """Test class generation example runs."""
        example = EXAMPLES_DIR / "typescript" / "02-class-generation.py"
        assert example.exists()

        result = subprocess.run(
            [sys.executable, str(example)],
            capture_output=True,
            timeout=30,
        )

        assert result.returncode == 0

    def test_03_interface_generation(self):
        """Test interface generation example runs."""
        example = EXAMPLES_DIR / "typescript" / "03-interface-generation.py"
        assert example.exists()

        result = subprocess.run(
            [sys.executable, str(example)],
            capture_output=True,
            timeout=30,
        )

        assert result.returncode == 0

    def test_04_api_endpoint(self):
        """Test API endpoint example runs."""
        example = EXAMPLES_DIR / "typescript" / "04-api-endpoint.py"
        assert example.exists()

        result = subprocess.run(
            [sys.executable, str(example)],
            capture_output=True,
            timeout=30,
        )

        assert result.returncode == 0

    def test_05_type_safe_refactor(self):
        """Test type-safe refactoring example runs."""
        example = EXAMPLES_DIR / "typescript" / "05-type-safe-refactor.py"
        assert example.exists()

        result = subprocess.run(
            [sys.executable, str(example)],
            capture_output=True,
            timeout=30,
        )

        assert result.returncode == 0


class TestAdvancedExamples:
    """Tests for advanced examples."""

    def test_01_api_generation(self):
        """Test API generation example runs."""
        example = EXAMPLES_DIR / "advanced" / "01-api-generation.py"
        assert example.exists()

        result = subprocess.run(
            [sys.executable, str(example)],
            capture_output=True,
            timeout=30,
        )

        assert result.returncode == 0
        assert b"Example complete" in result.stdout

    def test_02_code_refactoring(self):
        """Test code refactoring example runs."""
        example = EXAMPLES_DIR / "advanced" / "02-code-refactoring.py"
        assert example.exists()

        result = subprocess.run(
            [sys.executable, str(example)],
            capture_output=True,
            timeout=30,
        )

        assert result.returncode == 0

    def test_03_test_generation(self):
        """Test test generation example runs."""
        example = EXAMPLES_DIR / "advanced" / "03-test-generation.py"
        assert example.exists()

        result = subprocess.run(
            [sys.executable, str(example)],
            capture_output=True,
            timeout=30,
        )

        assert result.returncode == 0


class TestIntegrationExamples:
    """Tests for integration examples."""

    def test_01_github_bot(self):
        """Test GitHub bot example runs."""
        example = EXAMPLES_DIR / "integration" / "01-github-bot.py"
        assert example.exists()

        result = subprocess.run(
            [sys.executable, str(example)],
            capture_output=True,
            timeout=30,
        )

        assert result.returncode == 0
        assert b"Example complete" in result.stdout

    def test_02_ci_pipeline(self):
        """Test CI pipeline example runs."""
        example = EXAMPLES_DIR / "integration" / "02-ci-pipeline.py"
        assert example.exists()

        result = subprocess.run(
            [sys.executable, str(example)],
            capture_output=True,
            timeout=30,
        )

        assert result.returncode == 0
        assert b"Example complete" in result.stdout


class TestExampleStructure:
    """Tests for example structure and documentation."""

    def test_all_basic_examples_exist(self):
        """Test all basic examples exist."""
        expected = [
            "01-function-generation.py",
            "02-class-generation.py",
            "03-interface-generation.py",
            "04-api-endpoint.py",
            "05-type-safe-refactor.py",
        ]

        for filename in expected:
            path = EXAMPLES_DIR / "typescript" / filename
            assert path.exists(), f"Missing example: {filename}"

    def test_all_advanced_examples_exist(self):
        """Test all advanced examples exist."""
        expected = [
            "01-api-generation.py",
            "02-code-refactoring.py",
            "03-test-generation.py",
        ]

        for filename in expected:
            path = EXAMPLES_DIR / "advanced" / filename
            assert path.exists(), f"Missing example: {filename}"

    def test_all_integration_examples_exist(self):
        """Test all integration examples exist."""
        expected = [
            "01-github-bot.py",
            "02-ci-pipeline.py",
        ]

        for filename in expected:
            path = EXAMPLES_DIR / "integration" / filename
            assert path.exists(), f"Missing example: {filename}"
