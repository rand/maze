"""
Multi-level validation pipeline.

Orchestrates validation across syntax, types, tests, and lint with early exit,
parallel execution, and comprehensive diagnostics collection.
"""

from dataclasses import dataclass, field
from typing import Optional, Any, Literal
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from maze.validation.syntax import SyntaxValidator, SyntaxValidationResult
from maze.validation.types import TypeValidator, TypeValidationResult
from maze.validation.tests import TestValidator, TestValidationResult
from maze.validation.lint import LintValidator, LintValidationResult, LintRules
from maze.integrations.rune import RuneExecutor


@dataclass
class Diagnostic:
    """Validation diagnostic (error, warning, info)."""

    level: Literal["error", "warning", "info"]
    message: str
    line: int
    column: int
    code: Optional[str] = None
    source: str = ""  # "syntax", "type", "test", "lint", "security"
    suggested_fix: Optional[str] = None
    context: Optional[str] = None  # Surrounding code


@dataclass
class TypeContext:
    """Type environment for validation."""

    variables: dict[str, Any] = field(default_factory=dict)
    functions: dict[str, tuple[list[Any], Any]] = field(default_factory=dict)

    def copy(self) -> "TypeContext":
        """Create a copy of the type context."""
        return TypeContext(
            variables=self.variables.copy(), functions=self.functions.copy()
        )


@dataclass
class ValidationContext:
    """Context for validation."""

    type_context: Optional[TypeContext] = None
    tests: Optional[str] = None
    lint_rules: Optional[LintRules] = None
    timeout_ms: int = 5000


@dataclass
class ValidationResult:
    """Combined validation result."""

    success: bool
    diagnostics: list[Diagnostic]
    validation_time_ms: float
    stages_passed: list[str]  # ["syntax", "types", ...]
    stages_failed: list[str]
    stage_results: dict[str, Any] = field(default_factory=dict)


class ValidationPipeline:
    """Multi-level validation pipeline with early exit."""

    def __init__(
        self,
        syntax_validator: Optional[SyntaxValidator] = None,
        type_validator: Optional[TypeValidator] = None,
        test_validator: Optional[TestValidator] = None,
        lint_validator: Optional[LintValidator] = None,
        pedantic_raven: Optional[Any] = None,
        parallel_validation: bool = True,
    ):
        """
        Initialize validation pipeline.

        Args:
            syntax_validator: Syntax validator (created if None)
            type_validator: Type validator (created if None)
            test_validator: Test validator (created if None)
            lint_validator: Lint validator (created if None)
            pedantic_raven: Optional final quality gate
            parallel_validation: Run syntax and lint in parallel

        Example:
            >>> pipeline = ValidationPipeline()
            >>> context = ValidationContext()
            >>> result = pipeline.validate("def foo(): pass", "python", context)
        """
        self.syntax_validator = syntax_validator or SyntaxValidator()
        self.type_validator = type_validator or TypeValidator()
        self.test_validator = test_validator or TestValidator(sandbox=RuneExecutor())
        self.lint_validator = lint_validator or LintValidator()
        self.pedantic_raven = pedantic_raven
        self.parallel_validation = parallel_validation

        # Statistics
        self.stats = {
            "total_validations": 0,
            "successful_validations": 0,
            "syntax_failures": 0,
            "type_failures": 0,
            "test_failures": 0,
            "lint_failures": 0,
            "total_time_ms": 0.0,
        }

    def validate(
        self,
        code: str,
        language: str,
        context: Optional[ValidationContext] = None,
        stages: Optional[list[str]] = None,
    ) -> ValidationResult:
        """
        Run validation pipeline.

        Args:
            code: Source code to validate
            language: Programming language
            context: Validation context (types, tests, rules)
            stages: Stages to run (default: all)

        Returns:
            Combined validation result

        Example:
            >>> pipeline = ValidationPipeline()
            >>> context = ValidationContext(
            ...     type_context=TypeContext(),
            ...     tests="def test_foo(): assert foo() == 42",
            ...     lint_rules=LintRules.default()
            ... )
            >>> result = pipeline.validate(code, "python", context)
            >>> assert result.success or len(result.diagnostics) > 0
        """
        start_time = time.perf_counter()
        context = context or ValidationContext()

        # Determine which stages to run
        all_stages = ["syntax", "types", "tests", "lint"]
        if self.pedantic_raven:
            all_stages.append("security")

        run_stages = stages if stages is not None else all_stages

        diagnostics: list[Diagnostic] = []
        stages_passed: list[str] = []
        stages_failed: list[str] = []
        stage_results: dict[str, Any] = {}

        # Run validators in order with early exit optimization
        if "syntax" in run_stages:
            syntax_result = self._run_syntax(code, language)
            stage_results["syntax"] = syntax_result

            if syntax_result.success:
                stages_passed.append("syntax")
            else:
                stages_failed.append("syntax")
                diagnostics.extend(self._convert_diagnostics(syntax_result.diagnostics))
                self.stats["syntax_failures"] += 1

        # Type validation (requires syntax to pass for best results)
        if "types" in run_stages and (
            "syntax" not in run_stages or "syntax" in stages_passed
        ):
            type_result = self._run_types(
                code, language, context.type_context or TypeContext()
            )
            stage_results["types"] = type_result

            if type_result.success:
                stages_passed.append("types")
            else:
                stages_failed.append("types")
                diagnostics.extend(self._convert_diagnostics(type_result.diagnostics))
                self.stats["type_failures"] += 1

        # Parallel validation for tests and lint (if enabled and syntax passed)
        parallel_stages = []
        if self.parallel_validation and (
            "syntax" not in run_stages or "syntax" in stages_passed
        ):
            if "tests" in run_stages and context.tests:
                parallel_stages.append("tests")
            if "lint" in run_stages:
                parallel_stages.append("lint")

            if parallel_stages:
                parallel_results = self._run_parallel(
                    code, language, context, parallel_stages
                )

                for stage, result in parallel_results.items():
                    stage_results[stage] = result
                    if result.success:
                        stages_passed.append(stage)
                    else:
                        stages_failed.append(stage)
                        diagnostics.extend(
                            self._convert_diagnostics(result.diagnostics)
                        )
                        if stage == "tests":
                            self.stats["test_failures"] += 1
                        elif stage == "lint":
                            self.stats["lint_failures"] += 1
        else:
            # Sequential validation
            if "tests" in run_stages and context.tests:
                test_result = self._run_tests(
                    code, context.tests, language, context.timeout_ms
                )
                stage_results["tests"] = test_result

                if test_result.success:
                    stages_passed.append("tests")
                else:
                    stages_failed.append("tests")
                    diagnostics.extend(
                        self._convert_diagnostics(test_result.diagnostics)
                    )
                    self.stats["test_failures"] += 1

            if "lint" in run_stages:
                lint_result = self._run_lint(
                    code, language, context.lint_rules or LintRules.default()
                )
                stage_results["lint"] = lint_result

                if lint_result.success:
                    stages_passed.append("lint")
                else:
                    stages_failed.append("lint")
                    diagnostics.extend(
                        self._convert_diagnostics(lint_result.diagnostics)
                    )
                    self.stats["lint_failures"] += 1

        # Optional pedantic_raven security check
        if "security" in run_stages and self.pedantic_raven:
            security_result = self.pedantic_raven.review(code, language)
            stage_results["security"] = security_result

            if security_result.success:
                stages_passed.append("security")
            else:
                stages_failed.append("security")
                # Convert pedantic_raven findings to diagnostics
                for finding in security_result.security_findings:
                    diagnostics.append(
                        Diagnostic(
                            level="error" if finding.severity in ["critical", "high"] else "warning",
                            message=finding.message,
                            line=finding.line,
                            column=finding.column,
                            source="security",
                            code=finding.category,
                        )
                    )

        # Calculate overall success
        success = len(stages_failed) == 0 and len(run_stages) > 0

        validation_time_ms = (time.perf_counter() - start_time) * 1000

        # Update stats
        self.stats["total_validations"] += 1
        if success:
            self.stats["successful_validations"] += 1
        self.stats["total_time_ms"] += validation_time_ms

        return ValidationResult(
            success=success,
            diagnostics=diagnostics,
            validation_time_ms=validation_time_ms,
            stages_passed=stages_passed,
            stages_failed=stages_failed,
            stage_results=stage_results,
        )

    def validate_syntax(self, code: str, language: str) -> list[Diagnostic]:
        """
        Quick syntax-only validation.

        Args:
            code: Source code
            language: Programming language

        Returns:
            List of syntax diagnostics
        """
        result = self._run_syntax(code, language)
        return self._convert_diagnostics(result.diagnostics)

    def validate_types(
        self, code: str, language: str, context: Optional[TypeContext] = None
    ) -> list[Diagnostic]:
        """
        Type validation only.

        Args:
            code: Source code
            language: Programming language
            context: Type context

        Returns:
            List of type diagnostics
        """
        result = self._run_types(code, language, context or TypeContext())
        return self._convert_diagnostics(result.diagnostics)

    def validate_tests(
        self, code: str, tests: str, language: str, timeout_ms: int = 5000
    ) -> "TestResult":
        """
        Test execution only.

        Args:
            code: Source code
            tests: Test code
            language: Programming language
            timeout_ms: Execution timeout

        Returns:
            Test results
        """
        result = self._run_tests(code, tests, language, timeout_ms)
        return TestResult(
            success=result.success,
            diagnostics=self._convert_diagnostics(result.diagnostics),
            test_results=result.test_results,
            execution_time_ms=result.execution_time_ms,
        )

    def validate_lint(
        self, code: str, language: str, rules: Optional[LintRules] = None
    ) -> list[Diagnostic]:
        """
        Lint validation only.

        Args:
            code: Source code
            language: Programming language
            rules: Lint rules

        Returns:
            List of lint diagnostics
        """
        result = self._run_lint(code, language, rules or LintRules.default())
        return self._convert_diagnostics(result.diagnostics)

    def get_pipeline_stats(self) -> dict[str, Any]:
        """
        Get validation statistics.

        Returns:
            Statistics dictionary with counts and timings
        """
        avg_time = 0.0
        if self.stats["total_validations"] > 0:
            avg_time = self.stats["total_time_ms"] / self.stats["total_validations"]

        return {
            **self.stats,
            "average_validation_time_ms": avg_time,
            "success_rate": (
                self.stats["successful_validations"] / self.stats["total_validations"]
                if self.stats["total_validations"] > 0
                else 0.0
            ),
        }

    # Internal methods

    def _run_syntax(self, code: str, language: str) -> SyntaxValidationResult:
        """Run syntax validation."""
        return self.syntax_validator.validate(code, language)

    def _run_types(
        self, code: str, language: str, context: TypeContext
    ) -> TypeValidationResult:
        """Run type validation."""
        return self.type_validator.validate(code, language, context)

    def _run_tests(
        self, code: str, tests: str, language: str, timeout_ms: int
    ) -> TestValidationResult:
        """Run test validation."""
        return self.test_validator.validate(code, tests, language, timeout_ms)

    def _run_lint(
        self, code: str, language: str, rules: LintRules
    ) -> LintValidationResult:
        """Run lint validation."""
        return self.lint_validator.validate(code, language, rules)

    def _run_parallel(
        self, code: str, language: str, context: ValidationContext, stages: list[str]
    ) -> dict[str, Any]:
        """Run multiple stages in parallel."""
        results = {}

        with ThreadPoolExecutor(max_workers=len(stages)) as executor:
            futures = {}

            for stage in stages:
                if stage == "tests" and context.tests:
                    future = executor.submit(
                        self._run_tests,
                        code,
                        context.tests,
                        language,
                        context.timeout_ms,
                    )
                    futures[future] = "tests"
                elif stage == "lint":
                    future = executor.submit(
                        self._run_lint,
                        code,
                        language,
                        context.lint_rules or LintRules.default(),
                    )
                    futures[future] = "lint"

            for future in as_completed(futures):
                stage = futures[future]
                try:
                    results[stage] = future.result()
                except Exception as e:
                    # Create error result
                    results[stage] = self._create_error_result(stage, str(e))

        return results

    def _convert_diagnostics(self, diagnostics: list[Any]) -> list[Diagnostic]:
        """Convert validator-specific diagnostics to common format."""
        converted = []
        for d in diagnostics:
            if isinstance(d, Diagnostic):
                converted.append(d)
            else:
                # Convert from validator-specific diagnostic
                converted.append(
                    Diagnostic(
                        level=getattr(d, "level", "error"),
                        message=getattr(d, "message", str(d)),
                        line=getattr(d, "line", 0),
                        column=getattr(d, "column", 0),
                        code=getattr(d, "code", None),
                        source=getattr(d, "source", ""),
                        suggested_fix=getattr(d, "suggested_fix", None),
                        context=getattr(d, "context", None),
                    )
                )
        return converted

    def _create_error_result(self, stage: str, error: str) -> Any:
        """Create an error result for a failed stage."""
        from maze.validation.syntax import Diagnostic as SyntaxDiagnostic

        diagnostic = SyntaxDiagnostic(
            level="error",
            message=f"{stage} validation failed: {error}",
            line=0,
            column=0,
            source=stage,
        )

        if stage == "tests":
            from maze.validation.tests import TestResults

            return TestValidationResult(
                success=False,
                diagnostics=[diagnostic],
                test_results=TestResults(passed=0, failed=0, skipped=0, errors=1),
                execution_time_ms=0.0,
            )
        else:
            return LintValidationResult(
                success=False,
                diagnostics=[diagnostic],
                auto_fixable=[],
                validation_time_ms=0.0,
            )


@dataclass
class TestResult:
    """Test execution result."""

    success: bool
    diagnostics: list[Diagnostic]
    test_results: Any
    execution_time_ms: float
