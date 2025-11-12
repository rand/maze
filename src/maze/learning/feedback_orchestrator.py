"""
Feedback loop orchestrator for adaptive code generation.

Coordinates learning from all generation results.
"""

import time
from dataclasses import dataclass, field

from maze.integrations.mnemosyne import MnemosyneIntegration
from maze.learning.constraint_learning import (
    ConstraintLearningSystem,
    ConstraintRefinement,
    Feedback,
    GenerationResult,
    RepairResult,
    ValidationResult,
)
from maze.learning.pattern_mining import SemanticPattern, SyntacticPattern, TypePattern
from maze.learning.project_adaptation import ProjectAdaptationManager


@dataclass
class FeedbackResult:
    """Result of feedback processing."""

    pattern: SyntacticPattern | TypePattern | SemanticPattern | None
    score: float
    refinements: list[ConstraintRefinement]
    updated_weights: dict[str, float]


@dataclass
class FeedbackStats:
    """Feedback loop statistics."""

    total_feedback_events: int = 0
    positive_events: int = 0
    negative_events: int = 0
    average_score: float = 0.0
    refinements_applied: int = 0
    last_update: float = field(default_factory=time.time)


class FeedbackLoopOrchestrator:
    """
    Coordinate learning from generation results.

    Integrates:
    - ConstraintLearningSystem: Learn soft constraints
    - ProjectAdaptationManager: Adapt to project conventions
    - MnemosyneIntegration: Persist cross-session learning

    Performance target: <20ms per feedback
    """

    def __init__(
        self,
        learner: ConstraintLearningSystem,
        adapter: ProjectAdaptationManager,
        memory: MnemosyneIntegration,
        enable_auto_persist: bool = True,
    ):
        """
        Initialize feedback loop orchestrator.

        Args:
            learner: Constraint learning system
            adapter: Project adaptation manager
            memory: Mnemosyne integration
            enable_auto_persist: Auto-save to mnemosyne
        """
        self.learner = learner
        self.adapter = adapter
        self.memory = memory
        self.enable_auto_persist = enable_auto_persist
        self.stats = FeedbackStats()

    def process_feedback(
        self,
        generation: GenerationResult,
        validation: ValidationResult,
        repair: RepairResult | None = None,
        project_name: str | None = None,
    ) -> FeedbackResult:
        """
        Process feedback from generation outcome.

        Args:
            generation: Generation result
            validation: Validation result
            repair: Optional repair result
            project_name: Optional project identifier

        Returns:
            Feedback processing result

        Performance: <20ms
        """
        start_time = time.perf_counter()

        # Build feedback object
        feedback = Feedback(
            success=validation.success,
            generation_result=generation,
            validation_result=validation,
            repair_result=repair,
            score=self._compute_overall_score(validation, repair),
            feedback_type=self._classify_feedback(validation, repair),
        )

        # Update statistics
        self.stats.total_feedback_events += 1
        if feedback.success:
            self.stats.positive_events += 1
        else:
            self.stats.negative_events += 1

        # Update rolling average score
        self.stats.average_score = (
            self.stats.average_score * (self.stats.total_feedback_events - 1) + feedback.score
        ) / self.stats.total_feedback_events

        # Learn from feedback
        refinements = []
        if feedback.success:
            refinement = self.learner.learn_from_success(generation, validation)
            refinements.append(refinement)
        else:
            diagnostics = [
                {"severity": d.get("severity", "error"), "message": d.get("message", "")}
                for d in validation.diagnostics
            ]
            refinement = self.learner.learn_from_failure(generation, diagnostics)
            refinements.append(refinement)

        # Update project adaptation if project specified
        if project_name:
            self.adapter.update_from_feedback(project_name, feedback)

        # Extract patterns and update weights
        patterns = self._extract_patterns_from_result(generation)
        updated_weights = {}
        for pattern in patterns:
            new_weight = self.learner.update_weights(pattern, feedback)
            pattern_id = self.learner._pattern_to_id(pattern)
            updated_weights[pattern_id] = new_weight

        self.stats.refinements_applied += len(refinements)
        self.stats.last_update = time.time()

        result = FeedbackResult(
            pattern=patterns[0] if patterns else None,
            score=feedback.score,
            refinements=refinements,
            updated_weights=updated_weights,
        )

        # Auto-persist to mnemosyne
        if self.enable_auto_persist and project_name:
            namespace = f"project:{project_name}:feedback"
            self.persist_to_memory(result, namespace)

        processing_time_ms = (time.perf_counter() - start_time) * 1000
        if processing_time_ms >= 20:
            # Log warning but don't fail
            pass

        return result

    def _compute_overall_score(
        self, validation: ValidationResult, repair: RepairResult | None
    ) -> float:
        """
        Compute overall quality score.

        Returns:
            Score in range [-2, 2]
        """
        score = 0.0

        if validation.success:
            score += 1.0
        else:
            score -= 0.5

        if repair:
            if repair.success:
                # Penalize for needing repair
                score += 0.5 - (repair.attempts * 0.1)
            else:
                score -= 1.0

        # Test results
        if validation.test_results:
            total = validation.test_results.get("total", 0)
            passed = validation.test_results.get("passed", 0)
            if total > 0:
                score += (passed / total) - 0.5  # Normalized to [-0.5, 0.5]

        # Security violations
        critical_violations = [
            v for v in validation.security_violations if v.get("severity") == "critical"
        ]
        score -= len(critical_violations) * 2.0

        return max(-2.0, min(2.0, score))

    def _classify_feedback(self, validation: ValidationResult, repair: RepairResult | None) -> str:
        """
        Classify feedback type.

        Returns:
            "positive", "negative", or "neutral"
        """
        if validation.success and (not repair or repair.success):
            return "positive"
        elif not validation.success or (repair and not repair.success):
            return "negative"
        else:
            return "neutral"

    def _extract_patterns_from_result(
        self, generation: GenerationResult
    ) -> list[SyntacticPattern | TypePattern | SemanticPattern]:
        """
        Extract patterns from generation result.

        Returns:
            List of patterns found in generated code
        """
        patterns: list[SyntacticPattern | TypePattern | SemanticPattern] = []

        # Use pattern IDs from generation if available
        if generation.patterns_used:
            # Pattern IDs available - create stub patterns
            for pattern_id in generation.patterns_used:
                # Create a simple syntactic pattern as placeholder
                pattern = SyntacticPattern(
                    pattern_type="generated",
                    template=f"pattern_{pattern_id}",
                    frequency=1,
                    examples=[generation.code[:100]],
                    context={"pattern_id": pattern_id},
                )
                patterns.append(pattern)
        else:
            # Extract basic patterns from code
            import ast

            try:
                tree = ast.parse(generation.code)

                # Extract function patterns
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        pattern = SyntacticPattern(
                            pattern_type="function",
                            template=f"def {node.name}(...)",
                            frequency=1,
                            examples=[generation.code],
                            context={"args_count": len(node.args.args)},
                        )
                        patterns.append(pattern)
                        break  # Just use first function

                    elif isinstance(node, ast.ClassDef):
                        pattern = SyntacticPattern(
                            pattern_type="class",
                            template=f"class {node.name}",
                            frequency=1,
                            examples=[generation.code],
                            context={},
                        )
                        patterns.append(pattern)
                        break  # Just use first class

            except SyntaxError:
                # Can't parse - create generic pattern
                pattern = SyntacticPattern(
                    pattern_type="unknown",
                    template="...",
                    frequency=1,
                    examples=[generation.code[:100]],
                    context={},
                )
                patterns.append(pattern)

        return patterns

    def update_learning_state(
        self, feedback: FeedbackResult, project_name: str | None = None
    ) -> None:
        """
        Update learning state from feedback.

        Args:
            feedback: Feedback result
            project_name: Optional project identifier
        """
        # Apply refinements
        for refinement in feedback.refinements:
            if refinement.operation in ["add", "update"]:
                # Refinement already applied during process_feedback
                pass

        # Update statistics
        self.stats.last_update = time.time()

    def persist_to_memory(self, feedback: FeedbackResult, namespace: str) -> None:
        """
        Persist feedback to mnemosyne.

        Args:
            feedback: Feedback result
            namespace: Memory namespace
        """
        if feedback.pattern:
            # Determine importance based on score
            importance = int(max(1, min(10, (feedback.score + 2) * 2.5)))

            # Create tags
            tags = ["feedback"]
            if feedback.score > 0:
                tags.append("positive")
            elif feedback.score < 0:
                tags.append("negative")

            # Store pattern
            self.memory.store_pattern(
                pattern=feedback.pattern, namespace=namespace, importance=importance, tags=tags
            )

    def get_feedback_stats(self) -> FeedbackStats:
        """
        Get feedback loop statistics.

        Returns:
            Feedback statistics
        """
        return self.stats

    def reset_stats(self) -> None:
        """Reset feedback statistics."""
        self.stats = FeedbackStats()


__all__ = [
    "FeedbackLoopOrchestrator",
    "FeedbackResult",
    "FeedbackStats",
]
