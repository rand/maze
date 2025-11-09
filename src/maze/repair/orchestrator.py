"""
Repair orchestrator with adaptive strategy selection and constraint learning.

Analyzes validation failures, selects appropriate repair strategies,
refines constraints, and learns from successful repairs for future use.
"""

from dataclasses import dataclass, field
from typing import Optional, Any, Literal, Protocol
from enum import Enum
import time
import hashlib
import re

from maze.validation.pipeline import ValidationPipeline, Diagnostic, ValidationContext, TypeContext
from maze.validation.lint import LintRules


class RepairStrategy(Enum):
    """Repair strategies ordered by aggressiveness."""

    CONSTRAINT_TIGHTENING = "constraint_tightening"
    TYPE_NARROWING = "type_narrowing"
    EXAMPLE_BASED = "example_based"
    TEMPLATE_FALLBACK = "template_fallback"
    SIMPLIFY = "simplify"


@dataclass
class FailureAnalysis:
    """Analysis of validation failures."""

    syntax_errors: list[Diagnostic]
    type_errors: list[Diagnostic]
    test_errors: list[Diagnostic]
    lint_errors: list[Diagnostic]
    root_causes: list[str]
    failure_patterns: list[str]
    severity: Literal["low", "medium", "high"]


@dataclass
class ConstraintRefinement:
    """Constraint refinement for repair."""

    original_grammar: str
    refined_grammar: str
    refinement_type: str  # "regex", "structure", "type", "example"
    description: str


@dataclass
class RepairResult:
    """Result of repair attempt."""

    success: bool
    repaired_code: Optional[str]
    attempts: int
    strategies_used: list[str]
    diagnostics_resolved: list[Diagnostic]
    diagnostics_remaining: list[Diagnostic]
    repair_time_ms: float
    constraint_refinements: list[ConstraintRefinement]
    learned_patterns: list[str]


@dataclass
class RepairContext:
    """Context for repair."""

    type_context: Optional[TypeContext] = None
    validation_context: Optional[ValidationContext] = None
    original_prompt: str = ""
    max_attempts: int = 3


class CodeGenerator(Protocol):
    """Protocol for code generation with constraints."""

    def generate(
        self, prompt: str, grammar: str, language: str, context: Any
    ) -> str:
        """Generate code with grammar constraints."""
        ...


class ConstraintSynthesizer(Protocol):
    """Protocol for constraint synthesis."""

    def refine_grammar(
        self, grammar: str, diagnostics: list[Diagnostic], language: str
    ) -> str:
        """Refine grammar based on diagnostics."""
        ...


class RepairOrchestrator:
    """Adaptive repair loop with constraint learning."""

    def __init__(
        self,
        validator: ValidationPipeline,
        synthesizer: Optional[ConstraintSynthesizer] = None,
        generator: Optional[CodeGenerator] = None,
        max_attempts: int = 3,
        learning_enabled: bool = True,
    ):
        """
        Initialize repair orchestrator.

        Args:
            validator: Validation pipeline
            synthesizer: Constraint synthesizer (optional stub for now)
            generator: Provider adapter for regeneration (optional stub for now)
            max_attempts: Maximum repair attempts
            learning_enabled: Enable pattern learning

        Example:
            >>> from maze.validation.pipeline import ValidationPipeline
            >>> validator = ValidationPipeline()
            >>> orchestrator = RepairOrchestrator(validator)
        """
        self.validator = validator
        self.synthesizer = synthesizer
        self.generator = generator
        self.max_attempts = max_attempts
        self.learning_enabled = learning_enabled

        # Pattern learning database
        self.repair_patterns: dict[str, ConstraintRefinement] = {}

        # Statistics
        self.stats = {
            "total_repairs": 0,
            "successful_repairs": 0,
            "failed_repairs": 0,
            "total_attempts": 0,
            "patterns_learned": 0,
            "patterns_reused": 0,
            "avg_attempts": 0.0,
        }

    def repair(
        self,
        code: str,
        prompt: str,
        grammar: str,
        language: str,
        context: Optional[RepairContext] = None,
        max_attempts: Optional[int] = None,
    ) -> RepairResult:
        """
        Attempt to repair code with adaptive strategy.

        Args:
            code: Generated code with errors
            prompt: Original generation prompt
            grammar: Grammar used for generation
            language: Programming language
            context: Repair context (type context, test context, etc.)
            max_attempts: Override max attempts

        Returns:
            Repair result with final code or diagnostics

        Example:
            >>> orchestrator = RepairOrchestrator(validator)
            >>> result = orchestrator.repair(
            ...     code="def broken(",
            ...     prompt="Create add function",
            ...     grammar="",
            ...     language="python"
            ... )
            >>> assert result.attempts > 0
        """
        start_time = time.perf_counter()
        context = context or RepairContext()
        attempts_limit = max_attempts or context.max_attempts or self.max_attempts

        validation_context = context.validation_context or ValidationContext()

        # Initial validation
        val_result = self.validator.validate(code, language, validation_context)

        if val_result.success:
            # Code is already valid
            return RepairResult(
                success=True,
                repaired_code=code,
                attempts=0,
                strategies_used=[],
                diagnostics_resolved=[],
                diagnostics_remaining=[],
                repair_time_ms=(time.perf_counter() - start_time) * 1000,
                constraint_refinements=[],
                learned_patterns=[],
            )

        # Track repair attempt
        self.stats["total_repairs"] += 1

        current_code = code
        current_grammar = grammar
        all_diagnostics = val_result.diagnostics
        strategies_used = []
        refinements = []
        learned_patterns = []

        for attempt in range(1, attempts_limit + 1):
            self.stats["total_attempts"] += 1

            # Analyze failures
            analysis = self.analyze_diagnostics(all_diagnostics)

            # Check learned patterns
            pattern_key = self._pattern_key(analysis)
            if self.learning_enabled and pattern_key in self.repair_patterns:
                # Reuse learned pattern
                refinement = self.repair_patterns[pattern_key]
                current_grammar = refinement.refined_grammar
                self.stats["patterns_reused"] += 1
                learned_patterns.append(pattern_key)
            else:
                # Select strategy
                strategy = self.select_strategy(analysis, attempt, strategies_used)
                strategies_used.append(strategy.value)

                # Refine constraints
                refinement = self._refine_constraints_internal(
                    analysis, strategy, current_grammar, language
                )
                refinements.append(refinement)
                current_grammar = refinement.refined_grammar

            # Regenerate code (if generator available)
            if self.generator:
                try:
                    current_code = self.generator.generate(
                        prompt, current_grammar, language, context
                    )
                except Exception:
                    # Generator failed, keep current code
                    pass

            # Validate repaired code
            val_result = self.validator.validate(
                current_code, language, validation_context
            )

            if val_result.success:
                # Repair successful
                if self.learning_enabled and pattern_key not in self.repair_patterns:
                    # Learn pattern
                    self.repair_patterns[pattern_key] = refinement
                    self.stats["patterns_learned"] += 1

                self.stats["successful_repairs"] += 1
                self.stats["avg_attempts"] = (
                    self.stats["total_attempts"] / self.stats["total_repairs"]
                )

                return RepairResult(
                    success=True,
                    repaired_code=current_code,
                    attempts=attempt,
                    strategies_used=strategies_used,
                    diagnostics_resolved=all_diagnostics,
                    diagnostics_remaining=[],
                    repair_time_ms=(time.perf_counter() - start_time) * 1000,
                    constraint_refinements=refinements,
                    learned_patterns=learned_patterns,
                )

            # Update diagnostics
            all_diagnostics = val_result.diagnostics

        # Max attempts exceeded
        self.stats["failed_repairs"] += 1
        self.stats["avg_attempts"] = (
            self.stats["total_attempts"] / self.stats["total_repairs"]
        )

        return RepairResult(
            success=False,
            repaired_code=None,
            attempts=attempts_limit,
            strategies_used=strategies_used,
            diagnostics_resolved=[],
            diagnostics_remaining=all_diagnostics,
            repair_time_ms=(time.perf_counter() - start_time) * 1000,
            constraint_refinements=refinements,
            learned_patterns=learned_patterns,
        )

    def analyze_diagnostics(self, diagnostics: list[Diagnostic]) -> FailureAnalysis:
        """
        Extract root causes and patterns from diagnostics.

        Args:
            diagnostics: Validation diagnostics

        Returns:
            Failure analysis with categorized issues

        Analysis categories:
        - Syntax errors: missing tokens, malformed structure
        - Type errors: mismatches, missing annotations
        - Test errors: assertion failures, exceptions
        - Lint errors: style violations, complexity
        """
        syntax_errors = [d for d in diagnostics if d.source == "syntax"]
        type_errors = [d for d in diagnostics if d.source == "type"]
        test_errors = [d for d in diagnostics if d.source == "test"]
        lint_errors = [d for d in diagnostics if d.source == "lint"]

        # Extract root causes
        root_causes = []
        failure_patterns = []

        if syntax_errors:
            root_causes.append("syntax")
            # Common syntax patterns
            for error in syntax_errors:
                if "EOF" in error.message or "unexpected end" in error.message.lower():
                    failure_patterns.append("incomplete_structure")
                elif "missing" in error.message.lower():
                    failure_patterns.append("missing_token")
                elif "invalid syntax" in error.message.lower():
                    failure_patterns.append("malformed_syntax")

        if type_errors:
            root_causes.append("type_mismatch")
            # Common type patterns
            for error in type_errors:
                if "incompatible" in error.message.lower():
                    failure_patterns.append("type_incompatibility")
                elif "missing" in error.message.lower():
                    failure_patterns.append("missing_type_annotation")
                elif "cannot assign" in error.message.lower():
                    failure_patterns.append("invalid_assignment")

        if test_errors:
            root_causes.append("test_failure")
            # Common test patterns
            for error in test_errors:
                if "assertion" in error.message.lower():
                    failure_patterns.append("assertion_failure")
                elif "exception" in error.message.lower():
                    failure_patterns.append("runtime_exception")

        if lint_errors:
            root_causes.append("style_violation")
            # Common lint patterns
            for error in lint_errors:
                if "line length" in error.message.lower() or "too long" in error.message.lower():
                    failure_patterns.append("line_too_long")
                elif "complexity" in error.message.lower():
                    failure_patterns.append("high_complexity")

        # Determine severity
        if syntax_errors:
            severity = "high"
        elif type_errors:
            severity = "high"
        elif test_errors:
            severity = "medium"
        else:
            severity = "low"

        return FailureAnalysis(
            syntax_errors=syntax_errors,
            type_errors=type_errors,
            test_errors=test_errors,
            lint_errors=lint_errors,
            root_causes=list(set(root_causes)),
            failure_patterns=list(set(failure_patterns)),
            severity=severity,
        )

    def select_strategy(
        self,
        analysis: FailureAnalysis,
        attempt: int,
        previous_strategies: list[str],
    ) -> RepairStrategy:
        """
        Choose repair approach based on failures and attempt number.

        Args:
            analysis: Failure analysis
            attempt: Current attempt number
            previous_strategies: Previously tried strategies

        Returns:
            Selected repair strategy

        Strategies:
        - CONSTRAINT_TIGHTENING: Add regex/grammar rules
        - TYPE_NARROWING: Refine type constraints
        - EXAMPLE_BASED: Add positive examples
        - TEMPLATE_FALLBACK: Use structured template
        - SIMPLIFY: Reduce complexity
        """
        # Strategy progression based on attempt
        if attempt == 1:
            # First attempt: try constraint tightening (fastest)
            if analysis.syntax_errors:
                return RepairStrategy.CONSTRAINT_TIGHTENING
            elif analysis.type_errors:
                return RepairStrategy.TYPE_NARROWING
            elif analysis.test_errors:
                return RepairStrategy.EXAMPLE_BASED
            else:
                return RepairStrategy.CONSTRAINT_TIGHTENING

        elif attempt == 2:
            # Second attempt: try different approach
            if RepairStrategy.CONSTRAINT_TIGHTENING.value not in previous_strategies:
                return RepairStrategy.CONSTRAINT_TIGHTENING
            elif RepairStrategy.TYPE_NARROWING.value not in previous_strategies:
                return RepairStrategy.TYPE_NARROWING
            elif RepairStrategy.EXAMPLE_BASED.value not in previous_strategies:
                return RepairStrategy.EXAMPLE_BASED
            else:
                return RepairStrategy.TEMPLATE_FALLBACK

        else:
            # Third+ attempt: use template fallback or simplify
            if RepairStrategy.TEMPLATE_FALLBACK.value not in previous_strategies:
                return RepairStrategy.TEMPLATE_FALLBACK
            else:
                return RepairStrategy.SIMPLIFY

    def refine_constraints(
        self,
        analysis: FailureAnalysis,
        strategy: RepairStrategy,
        grammar: str,
        context: RepairContext,
    ) -> str:
        """
        Tighten grammar based on failures and strategy.

        Args:
            analysis: Failure analysis
            strategy: Selected repair strategy
            grammar: Current grammar
            context: Repair context

        Returns:
            Refined grammar

        Refinements:
        - Add forbidden patterns (for repeated errors)
        - Narrow type constraints
        - Add mandatory structure
        - Include positive examples
        """
        refinement = self._refine_constraints_internal(
            analysis, strategy, grammar, "python"
        )
        return refinement.refined_grammar

    def _refine_constraints_internal(
        self,
        analysis: FailureAnalysis,
        strategy: RepairStrategy,
        grammar: str,
        language: str,
    ) -> ConstraintRefinement:
        """Internal constraint refinement with full return value."""
        # If synthesizer available, use it
        if self.synthesizer:
            all_diagnostics = (
                analysis.syntax_errors
                + analysis.type_errors
                + analysis.test_errors
                + analysis.lint_errors
            )
            refined = self.synthesizer.refine_grammar(
                grammar, all_diagnostics, language
            )
            return ConstraintRefinement(
                original_grammar=grammar,
                refined_grammar=refined,
                refinement_type=strategy.value,
                description=f"Synthesizer refinement using {strategy.value}",
            )

        # Otherwise, use simple heuristics
        refined_grammar = grammar
        description = ""

        if strategy == RepairStrategy.CONSTRAINT_TIGHTENING:
            # Add structure requirements for syntax errors
            if analysis.syntax_errors:
                refined_grammar += "\n# Require complete structure"
                description = "Added structure requirements for syntax errors"
            else:
                refined_grammar += "\n# Tightened constraints"
                description = "General constraint tightening"

        elif strategy == RepairStrategy.TYPE_NARROWING:
            # Add type constraints for type errors
            refined_grammar += "\n# Narrowed type constraints"
            description = "Narrowed type constraints based on type errors"

        elif strategy == RepairStrategy.EXAMPLE_BASED:
            # Add example constraints for test errors
            refined_grammar += "\n# Added example constraints"
            description = "Added positive examples based on test failures"

        elif strategy == RepairStrategy.TEMPLATE_FALLBACK:
            # Use conservative template
            refined_grammar = self._get_template(language)
            description = "Fallback to conservative template"

        elif strategy == RepairStrategy.SIMPLIFY:
            # Simplify constraints
            refined_grammar = grammar.split("\n")[0] if grammar else ""
            description = "Simplified constraints to minimal form"

        return ConstraintRefinement(
            original_grammar=grammar,
            refined_grammar=refined_grammar,
            refinement_type=strategy.value,
            description=description,
        )

    def learn_pattern(
        self, failure: FailureAnalysis, successful_refinement: ConstraintRefinement
    ) -> None:
        """
        Store successful repair pattern for reuse.

        Args:
            failure: Original failure analysis
            successful_refinement: Constraint refinement that fixed the issue
        """
        if not self.learning_enabled:
            return

        pattern_key = self._pattern_key(failure)
        self.repair_patterns[pattern_key] = successful_refinement
        self.stats["patterns_learned"] += 1

    def get_repair_stats(self) -> dict[str, Any]:
        """
        Get repair statistics and learned patterns.

        Returns:
            Statistics dictionary with repair metrics
        """
        return {
            **self.stats,
            "learned_patterns_count": len(self.repair_patterns),
            "success_rate": (
                self.stats["successful_repairs"] / self.stats["total_repairs"]
                if self.stats["total_repairs"] > 0
                else 0.0
            ),
        }

    # Helper methods

    def _pattern_key(self, analysis: FailureAnalysis) -> str:
        """Generate unique key for failure pattern."""
        pattern_str = (
            f"{','.join(sorted(analysis.root_causes))}"
            f":{','.join(sorted(analysis.failure_patterns))}"
        )
        return hashlib.md5(pattern_str.encode()).hexdigest()[:8]

    def _get_template(self, language: str) -> str:
        """Get conservative template for language."""
        templates = {
            "python": "def function(): pass",
            "typescript": "function func(): void {}",
            "rust": "fn main() {}",
            "go": "func main() {}",
            "zig": "pub fn main() void {}",
        }
        return templates.get(language, "")
