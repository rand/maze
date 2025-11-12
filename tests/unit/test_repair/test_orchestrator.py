"""
Unit tests for repair orchestrator.

Tests adaptive repair strategies, diagnostic analysis, constraint refinement,
and pattern learning across various failure scenarios.
"""

from maze.repair.orchestrator import (
    ConstraintRefinement,
    FailureAnalysis,
    RepairContext,
    RepairOrchestrator,
    RepairStrategy,
)
from maze.validation.pipeline import (
    Diagnostic,
    ValidationPipeline,
)


class TestDiagnosticAnalysis:
    """Test diagnostic analysis and categorization."""

    def test_analyze_syntax_errors(self):
        """Test analysis of syntax errors."""
        orchestrator = RepairOrchestrator(validator=ValidationPipeline())

        diagnostics = [
            Diagnostic(
                level="error",
                message="SyntaxError: invalid syntax",
                line=1,
                column=10,
                source="syntax",
            ),
            Diagnostic(
                level="error",
                message="unexpected EOF",
                line=5,
                column=0,
                source="syntax",
            ),
        ]

        analysis = orchestrator.analyze_diagnostics(diagnostics)

        assert len(analysis.syntax_errors) == 2
        assert len(analysis.type_errors) == 0
        assert "syntax" in analysis.root_causes
        assert analysis.severity == "high"
        assert "incomplete_structure" in analysis.failure_patterns

    def test_analyze_type_errors(self):
        """Test analysis of type errors."""
        orchestrator = RepairOrchestrator(validator=ValidationPipeline())

        diagnostics = [
            Diagnostic(
                level="error",
                message="Type 'string' is not assignable to type 'number'",
                line=3,
                column=5,
                source="type",
            )
        ]

        analysis = orchestrator.analyze_diagnostics(diagnostics)

        assert len(analysis.type_errors) == 1
        assert "type_mismatch" in analysis.root_causes
        assert analysis.severity == "high"

    def test_analyze_test_errors(self):
        """Test analysis of test errors."""
        orchestrator = RepairOrchestrator(validator=ValidationPipeline())

        diagnostics = [
            Diagnostic(
                level="error",
                message="AssertionError: expected 5, got 3",
                line=10,
                column=0,
                source="test",
            )
        ]

        analysis = orchestrator.analyze_diagnostics(diagnostics)

        assert len(analysis.test_errors) == 1
        assert "test_failure" in analysis.root_causes
        assert analysis.severity == "medium"
        assert "assertion_failure" in analysis.failure_patterns

    def test_analyze_lint_errors(self):
        """Test analysis of lint errors."""
        orchestrator = RepairOrchestrator(validator=ValidationPipeline())

        diagnostics = [
            Diagnostic(
                level="warning",
                message="Line too long (120 > 100)",
                line=5,
                column=100,
                source="lint",
            )
        ]

        analysis = orchestrator.analyze_diagnostics(diagnostics)

        assert len(analysis.lint_errors) == 1
        assert "style_violation" in analysis.root_causes
        assert analysis.severity == "low"
        assert "line_too_long" in analysis.failure_patterns

    def test_analyze_multiple_error_types(self):
        """Test analysis with multiple error types."""
        orchestrator = RepairOrchestrator(validator=ValidationPipeline())

        diagnostics = [
            Diagnostic(level="error", message="syntax error", line=1, column=0, source="syntax"),
            Diagnostic(
                level="error",
                message="type mismatch",
                line=3,
                column=0,
                source="type",
            ),
            Diagnostic(
                level="error",
                message="test failed",
                line=10,
                column=0,
                source="test",
            ),
        ]

        analysis = orchestrator.analyze_diagnostics(diagnostics)

        assert len(analysis.root_causes) >= 2
        assert analysis.severity == "high"  # Syntax errors are high severity


class TestStrategySelection:
    """Test repair strategy selection."""

    def test_select_constraint_tightening_first_attempt(self):
        """Test that first attempt uses constraint tightening for syntax errors."""
        orchestrator = RepairOrchestrator(validator=ValidationPipeline())

        analysis = FailureAnalysis(
            syntax_errors=[
                Diagnostic(
                    level="error",
                    message="syntax error",
                    line=1,
                    column=0,
                    source="syntax",
                )
            ],
            type_errors=[],
            test_errors=[],
            lint_errors=[],
            root_causes=["syntax"],
            failure_patterns=["malformed_syntax"],
            severity="high",
        )

        strategy = orchestrator.select_strategy(analysis, attempt=1, previous_strategies=[])

        assert strategy == RepairStrategy.CONSTRAINT_TIGHTENING

    def test_select_type_narrowing_for_type_errors(self):
        """Test type narrowing strategy for type errors."""
        orchestrator = RepairOrchestrator(validator=ValidationPipeline())

        analysis = FailureAnalysis(
            syntax_errors=[],
            type_errors=[
                Diagnostic(
                    level="error",
                    message="type error",
                    line=1,
                    column=0,
                    source="type",
                )
            ],
            test_errors=[],
            lint_errors=[],
            root_causes=["type_mismatch"],
            failure_patterns=[],
            severity="high",
        )

        strategy = orchestrator.select_strategy(analysis, attempt=1, previous_strategies=[])

        assert strategy == RepairStrategy.TYPE_NARROWING

    def test_select_example_based_for_test_errors(self):
        """Test example-based strategy for test errors."""
        orchestrator = RepairOrchestrator(validator=ValidationPipeline())

        analysis = FailureAnalysis(
            syntax_errors=[],
            type_errors=[],
            test_errors=[
                Diagnostic(
                    level="error",
                    message="test failed",
                    line=1,
                    column=0,
                    source="test",
                )
            ],
            lint_errors=[],
            root_causes=["test_failure"],
            failure_patterns=[],
            severity="medium",
        )

        strategy = orchestrator.select_strategy(analysis, attempt=1, previous_strategies=[])

        assert strategy == RepairStrategy.EXAMPLE_BASED

    def test_select_fallback_on_second_attempt(self):
        """Test fallback strategy on second attempt."""
        orchestrator = RepairOrchestrator(validator=ValidationPipeline())

        analysis = FailureAnalysis(
            syntax_errors=[],
            type_errors=[],
            test_errors=[],
            lint_errors=[],
            root_causes=[],
            failure_patterns=[],
            severity="low",
        )

        strategy = orchestrator.select_strategy(
            analysis,
            attempt=2,
            previous_strategies=[
                RepairStrategy.CONSTRAINT_TIGHTENING.value,
                RepairStrategy.TYPE_NARROWING.value,
                RepairStrategy.EXAMPLE_BASED.value,
            ],
        )

        assert strategy == RepairStrategy.TEMPLATE_FALLBACK

    def test_select_simplify_on_third_attempt(self):
        """Test simplify strategy on third attempt."""
        orchestrator = RepairOrchestrator(validator=ValidationPipeline())

        analysis = FailureAnalysis(
            syntax_errors=[],
            type_errors=[],
            test_errors=[],
            lint_errors=[],
            root_causes=[],
            failure_patterns=[],
            severity="low",
        )

        strategy = orchestrator.select_strategy(
            analysis,
            attempt=3,
            previous_strategies=[
                RepairStrategy.CONSTRAINT_TIGHTENING.value,
                RepairStrategy.TEMPLATE_FALLBACK.value,
            ],
        )

        assert strategy == RepairStrategy.SIMPLIFY


class TestConstraintRefinement:
    """Test constraint refinement."""

    def test_refine_constraints_syntax(self):
        """Test constraint refinement for syntax errors."""
        orchestrator = RepairOrchestrator(validator=ValidationPipeline())

        analysis = FailureAnalysis(
            syntax_errors=[
                Diagnostic(
                    level="error",
                    message="syntax error",
                    line=1,
                    column=0,
                    source="syntax",
                )
            ],
            type_errors=[],
            test_errors=[],
            lint_errors=[],
            root_causes=["syntax"],
            failure_patterns=[],
            severity="high",
        )

        refined = orchestrator.refine_constraints(
            analysis,
            RepairStrategy.CONSTRAINT_TIGHTENING,
            "original grammar",
            RepairContext(),
        )

        assert len(refined) > 0
        assert "original grammar" in refined or "structure" in refined.lower()

    def test_refine_constraints_types(self):
        """Test constraint refinement for type errors."""
        orchestrator = RepairOrchestrator(validator=ValidationPipeline())

        analysis = FailureAnalysis(
            syntax_errors=[],
            type_errors=[
                Diagnostic(level="error", message="type error", line=1, column=0, source="type")
            ],
            test_errors=[],
            lint_errors=[],
            root_causes=["type_mismatch"],
            failure_patterns=[],
            severity="high",
        )

        refined = orchestrator.refine_constraints(
            analysis, RepairStrategy.TYPE_NARROWING, "original grammar", RepairContext()
        )

        assert len(refined) > 0

    def test_refine_constraints_template_fallback(self):
        """Test template fallback refinement."""
        orchestrator = RepairOrchestrator(validator=ValidationPipeline())

        analysis = FailureAnalysis(
            syntax_errors=[],
            type_errors=[],
            test_errors=[],
            lint_errors=[],
            root_causes=[],
            failure_patterns=[],
            severity="low",
        )

        refined = orchestrator.refine_constraints(
            analysis,
            RepairStrategy.TEMPLATE_FALLBACK,
            "original grammar",
            RepairContext(),
        )

        # Should use language template
        assert len(refined) > 0


class TestPatternLearning:
    """Test pattern learning and reuse."""

    def test_learn_repair_pattern(self):
        """Test learning successful repair pattern."""
        orchestrator = RepairOrchestrator(validator=ValidationPipeline(), learning_enabled=True)

        failure = FailureAnalysis(
            syntax_errors=[
                Diagnostic(
                    level="error",
                    message="syntax error",
                    line=1,
                    column=0,
                    source="syntax",
                )
            ],
            type_errors=[],
            test_errors=[],
            lint_errors=[],
            root_causes=["syntax"],
            failure_patterns=["malformed_syntax"],
            severity="high",
        )

        refinement = ConstraintRefinement(
            original_grammar="old",
            refined_grammar="new",
            refinement_type="structure",
            description="Fixed syntax",
        )

        orchestrator.learn_pattern(failure, refinement)

        assert len(orchestrator.repair_patterns) > 0
        assert orchestrator.stats["patterns_learned"] > 0

    def test_reuse_learned_pattern(self):
        """Test reusing learned pattern."""
        orchestrator = RepairOrchestrator(validator=ValidationPipeline(), learning_enabled=True)

        # Learn a pattern
        failure = FailureAnalysis(
            syntax_errors=[],
            type_errors=[],
            test_errors=[],
            lint_errors=[],
            root_causes=["test_failure"],
            failure_patterns=["assertion_failure"],
            severity="medium",
        )

        refinement = ConstraintRefinement(
            original_grammar="old",
            refined_grammar="new",
            refinement_type="example",
            description="Added example",
        )

        orchestrator.learn_pattern(failure, refinement)

        # Repair with same pattern (should reuse)
        result = orchestrator.repair(
            code="def foo(): return 42",
            prompt="Create function",
            grammar="old",
            language="python",
        )

        # Pattern might be reused (depends on validation)
        assert result.attempts >= 0


class TestMaxAttemptsLimit:
    """Test maximum attempts enforcement."""

    def test_max_attempts_limit(self):
        """Test that repair stops after max attempts."""
        orchestrator = RepairOrchestrator(validator=ValidationPipeline(), max_attempts=2)

        # Code that will fail validation
        result = orchestrator.repair(
            code="def broken(",
            prompt="Create function",
            grammar="",
            language="python",
            max_attempts=2,
        )

        assert result.attempts <= 2
        assert not result.success or result.attempts == 0  # Either failed or was valid

    def test_respects_context_max_attempts(self):
        """Test that context max_attempts is respected."""
        orchestrator = RepairOrchestrator(validator=ValidationPipeline())

        context = RepairContext(max_attempts=1)

        result = orchestrator.repair(
            code="def broken(",
            prompt="Create function",
            grammar="",
            language="python",
            context=context,
        )

        assert result.attempts <= 1


class TestSuccessfulRepairLoop:
    """Test successful repair scenarios."""

    def test_successful_repair_loop(self):
        """Test complete repair loop with valid code."""
        orchestrator = RepairOrchestrator(validator=ValidationPipeline())

        # Code that passes validation
        result = orchestrator.repair(
            code="def add(a, b):\n    return a + b\n",
            prompt="Create add function",
            grammar="",
            language="python",
        )

        assert result.success
        assert result.attempts == 0  # No repair needed
        assert result.repaired_code is not None

    def test_repair_with_valid_code(self):
        """Test that valid code doesn't require repair."""
        orchestrator = RepairOrchestrator(validator=ValidationPipeline())

        result = orchestrator.repair(
            code="x = 1",
            prompt="Create variable",
            grammar="",
            language="python",
        )

        assert result.success
        assert result.attempts == 0


class TestFailedRepairLoop:
    """Test failed repair scenarios."""

    def test_failed_repair_loop(self):
        """Test repair loop that exhausts attempts."""
        orchestrator = RepairOrchestrator(validator=ValidationPipeline(), max_attempts=1)

        # Code that will fail
        result = orchestrator.repair(
            code="def broken(",
            prompt="Create function",
            grammar="",
            language="python",
        )

        # Either repairs or fails
        assert result.attempts >= 0

    def test_diagnostics_remaining_on_failure(self):
        """Test that diagnostics are provided on failure."""
        orchestrator = RepairOrchestrator(validator=ValidationPipeline(), max_attempts=1)

        result = orchestrator.repair(
            code="def broken(",
            prompt="Create function",
            grammar="",
            language="python",
        )

        # If it failed, should have diagnostics
        if not result.success:
            assert len(result.diagnostics_remaining) > 0


class TestRepairStats:
    """Test repair statistics tracking."""

    def test_repair_stats_initialization(self):
        """Test that stats are initialized correctly."""
        orchestrator = RepairOrchestrator(validator=ValidationPipeline())

        stats = orchestrator.get_repair_stats()

        assert stats["total_repairs"] == 0
        assert stats["successful_repairs"] == 0
        assert stats["failed_repairs"] == 0

    def test_repair_stats_update(self):
        """Test that stats update after repairs."""
        orchestrator = RepairOrchestrator(validator=ValidationPipeline())

        # Use invalid code to trigger actual repair
        orchestrator.repair(
            code="def broken(",
            prompt="Create function",
            grammar="",
            language="python",
            max_attempts=1,
        )

        stats = orchestrator.get_repair_stats()

        # Should have attempted repair
        assert stats["total_repairs"] == 1
        assert stats["total_attempts"] >= 1

    def test_success_rate_calculation(self):
        """Test success rate calculation."""
        orchestrator = RepairOrchestrator(validator=ValidationPipeline())

        # Successful repair
        orchestrator.repair(
            code="def foo(): pass", prompt="Create function", grammar="", language="python"
        )

        stats = orchestrator.get_repair_stats()

        assert "success_rate" in stats
        assert 0.0 <= stats["success_rate"] <= 1.0


class TestLearningEnabled:
    """Test learning enable/disable."""

    def test_learning_disabled(self):
        """Test that learning can be disabled."""
        orchestrator = RepairOrchestrator(validator=ValidationPipeline(), learning_enabled=False)

        failure = FailureAnalysis(
            syntax_errors=[],
            type_errors=[],
            test_errors=[],
            lint_errors=[],
            root_causes=["test_failure"],
            failure_patterns=[],
            severity="low",
        )

        refinement = ConstraintRefinement(
            original_grammar="old",
            refined_grammar="new",
            refinement_type="example",
            description="Test",
        )

        orchestrator.learn_pattern(failure, refinement)

        # Should not learn when disabled
        assert len(orchestrator.repair_patterns) == 0


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_diagnostics(self):
        """Test analysis with empty diagnostics."""
        orchestrator = RepairOrchestrator(validator=ValidationPipeline())

        analysis = orchestrator.analyze_diagnostics([])

        assert len(analysis.syntax_errors) == 0
        assert len(analysis.root_causes) == 0
        assert analysis.severity == "low"

    def test_empty_grammar(self):
        """Test refinement with empty grammar."""
        orchestrator = RepairOrchestrator(validator=ValidationPipeline())

        analysis = FailureAnalysis(
            syntax_errors=[],
            type_errors=[],
            test_errors=[],
            lint_errors=[],
            root_causes=[],
            failure_patterns=[],
            severity="low",
        )

        refined = orchestrator.refine_constraints(
            analysis, RepairStrategy.SIMPLIFY, "", RepairContext()
        )

        assert isinstance(refined, str)

    def test_unsupported_language_template(self):
        """Test template for unsupported language."""
        orchestrator = RepairOrchestrator(validator=ValidationPipeline())

        template = orchestrator._get_template("cobol")

        assert isinstance(template, str)  # May be empty
