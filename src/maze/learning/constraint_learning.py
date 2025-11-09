"""
Constraint learning system for adaptive code generation.

Learns soft constraints from patterns and generation feedback.
"""

import ast
import hashlib
import json
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from maze.learning.pattern_mining import (
    PatternSet,
    SyntacticPattern,
    TypePattern,
    SemanticPattern
)


@dataclass
class ConstraintRefinement:
    """Constraint update from learning."""
    constraint_type: str  # "syntactic", "type", "semantic", "style"
    operation: str  # "add", "update", "remove", "reweight"
    constraint_data: dict[str, Any]
    weight: float  # 0-1, higher = stronger preference
    rationale: str  # Why this refinement was made
    source: str  # "pattern_mining", "feedback", "user"


@dataclass
class GenerationResult:
    """Result from code generation."""
    code: str
    language: str
    generation_time_ms: float
    patterns_used: list[str] = field(default_factory=list)


@dataclass
class ValidationResult:
    """Result from validation."""
    success: bool
    diagnostics: list[dict[str, Any]] = field(default_factory=list)
    test_results: Optional[dict[str, Any]] = None
    security_violations: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class RepairResult:
    """Result from repair attempts."""
    attempts: int
    success: bool
    final_code: Optional[str] = None


@dataclass
class Feedback:
    """Feedback from generation outcome."""
    success: bool
    generation_result: GenerationResult
    validation_result: ValidationResult
    repair_result: Optional[RepairResult]
    score: float  # Overall quality score
    feedback_type: str  # "positive", "negative", "neutral"


@dataclass
class LearningEvent:
    """Record of a learning event."""
    timestamp: float
    event_type: str  # "weight_increase", "weight_decrease", "constraint_added", "constraint_removed"
    pattern_id: str
    old_weight: float
    new_weight: float
    reason: str


class ConstraintLearningSystem:
    """
    Learn soft constraints from feedback and patterns.

    Maintains weighted constraints and adapts them based on:
    - Successful generation (boost weights)
    - Failed generation (reduce weights)
    - Pattern mining (discover new constraints)
    - Periodic decay (prevent over-fitting)
    """

    def __init__(
        self,
        learning_rate: float = 0.1,
        min_score: float = 0.1,
        max_constraints: int = 10000,
        decay_rate: float = 0.01
    ):
        """
        Initialize constraint learning system.

        Args:
            learning_rate: Weight update rate (0-1)
            min_score: Minimum score to keep constraint
            max_constraints: Maximum constraints to maintain
            decay_rate: Periodic score decay rate
        """
        self.learning_rate = learning_rate
        self.min_score = min_score
        self.max_constraints = max_constraints
        self.decay_rate = decay_rate

        # Core state
        self.constraints: dict[str, float] = {}  # constraint_id -> weight
        self.constraint_metadata: dict[str, dict[str, Any]] = {}  # constraint_id -> metadata
        self.learning_history: list[LearningEvent] = []

        # Statistics
        self.stats = {
            "total_feedback": 0,
            "successful_feedback": 0,
            "failed_feedback": 0,
            "constraints_added": 0,
            "constraints_removed": 0,
            "weight_updates": 0,
        }

    def _pattern_to_id(self, pattern: SyntacticPattern | TypePattern | SemanticPattern) -> str:
        """Generate unique ID for pattern."""
        if isinstance(pattern, SyntacticPattern):
            key = f"syntactic:{pattern.pattern_type}:{pattern.template}"
        elif isinstance(pattern, TypePattern):
            key = f"type:{pattern.signature}"
        elif isinstance(pattern, SemanticPattern):
            key = f"semantic:{pattern.intent}:{pattern.structure}"
        else:
            key = str(pattern)

        return f"pat-{hashlib.md5(key.encode()).hexdigest()[:12]}"

    def _extract_patterns_from_code(self, code: str) -> list[str]:
        """
        Extract pattern IDs from generated code.

        Returns:
            List of pattern IDs found in code
        """
        pattern_ids = []

        try:
            tree = ast.parse(code)

            # Extract function patterns
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    pattern = SyntacticPattern(
                        pattern_type="function",
                        template=f"def {node.name}(...)",
                        frequency=1,
                        examples=[],
                        context={"args_count": len(node.args.args)}
                    )
                    pattern_ids.append(self._pattern_to_id(pattern))

                elif isinstance(node, ast.ClassDef):
                    pattern = SyntacticPattern(
                        pattern_type="class",
                        template=f"class {node.name}",
                        frequency=1,
                        examples=[],
                        context={}
                    )
                    pattern_ids.append(self._pattern_to_id(pattern))

                elif isinstance(node, ast.Try):
                    pattern = SemanticPattern(
                        intent="error_handling",
                        structure="try-except",
                        implementations=[],
                        frequency=1
                    )
                    pattern_ids.append(self._pattern_to_id(pattern))

        except SyntaxError:
            # If code doesn't parse, extract basic patterns
            if "def " in code:
                pattern = SyntacticPattern(
                    pattern_type="function",
                    template="def ...",
                    frequency=1,
                    examples=[],
                    context={}
                )
                pattern_ids.append(self._pattern_to_id(pattern))

        return pattern_ids

    def _classify_failure(self, diagnostics: list[dict[str, Any]]) -> str:
        """
        Classify failure type from diagnostics.

        Returns:
            Failure type: "syntax", "type", "semantic", "test", "security"
        """
        if not diagnostics:
            return "unknown"

        for diag in diagnostics:
            severity = diag.get("severity", "").lower()
            message = diag.get("message", "").lower()

            # Check specific types first before generic error
            if "security" in message or "vulnerability" in message:
                return "security"
            elif "test" in message or "assertion" in message:
                return "test"
            elif "type" in message:
                return "type"
            elif "syntax" in message or severity == "error":
                return "syntax"

        return "semantic"

    def _compute_penalty(self, failure_type: str) -> float:
        """
        Compute penalty based on failure type.

        Returns:
            Penalty value (higher = more severe)
        """
        penalties = {
            "syntax": 0.5,
            "type": 0.4,
            "semantic": 0.3,
            "test": 0.2,
            "security": 1.0,  # Highest penalty
            "unknown": 0.1,
        }
        return penalties.get(failure_type, 0.1)

    def _compute_score_delta(self, feedback: Feedback) -> float:
        """
        Compute score change from feedback.

        Returns:
            Score delta in range [-2, 2]
        """
        score = 0.0

        if feedback.validation_result.success:
            score += 1.0

        if feedback.repair_result:
            # Fewer repair attempts = better
            score += max(0, 1.0 - (feedback.repair_result.attempts * 0.25))

        # Test results
        if feedback.validation_result.test_results:
            test_results = feedback.validation_result.test_results
            total = test_results.get("total", 0)
            passed = test_results.get("passed", 0)
            if total > 0:
                score += (passed / total)

        # Security (critical)
        security_violations = feedback.validation_result.security_violations
        critical_violations = [
            v for v in security_violations
            if v.get("severity") == "critical"
        ]
        score -= len(critical_violations) * 2.0

        return max(-2.0, min(2.0, score))  # Clamp to [-2, 2]

    def learn_from_success(
        self,
        generation_result: GenerationResult,
        validation_result: ValidationResult
    ) -> ConstraintRefinement:
        """
        Learn from successful generation.

        Args:
            generation_result: Successful generation
            validation_result: Passing validation

        Returns:
            Constraint refinement to apply
        """
        self.stats["total_feedback"] += 1
        self.stats["successful_feedback"] += 1

        feedback = Feedback(
            success=True,
            generation_result=generation_result,
            validation_result=validation_result,
            repair_result=None,
            score=1.0,
            feedback_type="positive"
        )

        score_delta = self._compute_score_delta(feedback)

        # Extract patterns from successful code
        patterns_used = self._extract_patterns_from_code(generation_result.code)

        # Boost weights for successful patterns
        updated_count = 0
        for pattern_id in patterns_used:
            current_weight = self.constraints.get(pattern_id, 0.5)
            new_weight = min(1.0, current_weight + (self.learning_rate * score_delta))

            if new_weight != current_weight:
                self.constraints[pattern_id] = new_weight
                self.stats["weight_updates"] += 1
                updated_count += 1

                self.learning_history.append(LearningEvent(
                    timestamp=time.time(),
                    event_type="weight_increase",
                    pattern_id=pattern_id,
                    old_weight=current_weight,
                    new_weight=new_weight,
                    reason=f"successful_generation_score_{score_delta:.2f}"
                ))

        return ConstraintRefinement(
            constraint_type="mixed",
            operation="update",
            constraint_data={"patterns_updated": updated_count},
            weight=score_delta,
            rationale=f"Boosted {updated_count} patterns from successful generation",
            source="feedback"
        )

    def learn_from_failure(
        self,
        generation_result: GenerationResult,
        diagnostics: list[dict[str, Any]]
    ) -> ConstraintRefinement:
        """
        Learn from failed generation.

        Args:
            generation_result: Failed generation
            diagnostics: Validation diagnostics

        Returns:
            Constraint refinement to prevent failure
        """
        self.stats["total_feedback"] += 1
        self.stats["failed_feedback"] += 1

        # Extract patterns from failed code
        patterns_used = self._extract_patterns_from_code(generation_result.code)

        # Classify failure
        failure_type = self._classify_failure(diagnostics)
        penalty = self._compute_penalty(failure_type)

        # Reduce weights for patterns leading to failures
        updated_count = 0
        for pattern_id in patterns_used:
            if pattern_id in self.constraints:
                current_weight = self.constraints[pattern_id]
                new_weight = max(0.0, current_weight - (self.learning_rate * penalty))

                if new_weight != current_weight:
                    self.constraints[pattern_id] = new_weight
                    self.stats["weight_updates"] += 1
                    updated_count += 1

                    self.learning_history.append(LearningEvent(
                        timestamp=time.time(),
                        event_type="weight_decrease",
                        pattern_id=pattern_id,
                        old_weight=current_weight,
                        new_weight=new_weight,
                        reason=f"failure_{failure_type}"
                    ))

        return ConstraintRefinement(
            constraint_type="mixed",
            operation="update",
            constraint_data={"patterns_updated": updated_count, "failure_type": failure_type},
            weight=-penalty,
            rationale=f"Penalized {updated_count} patterns from {failure_type} failure",
            source="feedback"
        )

    def learn_from_patterns(
        self,
        patterns: PatternSet
    ) -> list[ConstraintRefinement]:
        """
        Create constraints from mined patterns.

        Args:
            patterns: Mined patterns

        Returns:
            List of constraint refinements
        """
        refinements: list[ConstraintRefinement] = []

        # Process syntactic patterns
        for pattern in patterns.syntactic:
            pattern_id = self._pattern_to_id(pattern)

            if pattern_id not in self.constraints:
                # New pattern - add with weight based on frequency
                weight = min(1.0, pattern.frequency / 10.0)  # Normalize frequency
                self.constraints[pattern_id] = weight
                self.constraint_metadata[pattern_id] = {
                    "pattern_type": pattern.pattern_type,
                    "template": pattern.template,
                    "frequency": pattern.frequency,
                    "source": "pattern_mining"
                }
                self.stats["constraints_added"] += 1

                refinements.append(ConstraintRefinement(
                    constraint_type="syntactic",
                    operation="add",
                    constraint_data={"pattern_id": pattern_id, "template": pattern.template},
                    weight=weight,
                    rationale=f"New syntactic pattern with frequency {pattern.frequency}",
                    source="pattern_mining"
                ))

        # Process type patterns
        for pattern in patterns.type_patterns:
            pattern_id = self._pattern_to_id(pattern)

            if pattern_id not in self.constraints:
                weight = min(1.0, pattern.frequency / 10.0)
                self.constraints[pattern_id] = weight
                self.constraint_metadata[pattern_id] = {
                    "signature": pattern.signature,
                    "frequency": pattern.frequency,
                    "source": "pattern_mining"
                }
                self.stats["constraints_added"] += 1

                refinements.append(ConstraintRefinement(
                    constraint_type="type",
                    operation="add",
                    constraint_data={"pattern_id": pattern_id, "signature": pattern.signature},
                    weight=weight,
                    rationale=f"New type pattern with frequency {pattern.frequency}",
                    source="pattern_mining"
                ))

        # Process semantic patterns
        for pattern in patterns.semantic:
            pattern_id = self._pattern_to_id(pattern)

            if pattern_id not in self.constraints:
                weight = min(1.0, pattern.frequency / 10.0)
                self.constraints[pattern_id] = weight
                self.constraint_metadata[pattern_id] = {
                    "intent": pattern.intent,
                    "structure": pattern.structure,
                    "frequency": pattern.frequency,
                    "source": "pattern_mining"
                }
                self.stats["constraints_added"] += 1

                refinements.append(ConstraintRefinement(
                    constraint_type="semantic",
                    operation="add",
                    constraint_data={"pattern_id": pattern_id, "intent": pattern.intent},
                    weight=weight,
                    rationale=f"New semantic pattern with frequency {pattern.frequency}",
                    source="pattern_mining"
                ))

        return refinements

    def update_weights(
        self,
        pattern: SyntacticPattern | TypePattern | SemanticPattern,
        feedback: Feedback
    ) -> float:
        """
        Update pattern weight based on feedback.

        Args:
            pattern: Pattern to update
            feedback: Feedback to incorporate

        Returns:
            New weight value
        """
        pattern_id = self._pattern_to_id(pattern)
        current_weight = self.constraints.get(pattern_id, 0.5)

        score_delta = self._compute_score_delta(feedback)
        new_weight = current_weight + (self.learning_rate * score_delta)
        new_weight = max(0.0, min(1.0, new_weight))  # Clamp to [0, 1]

        self.constraints[pattern_id] = new_weight
        self.stats["weight_updates"] += 1

        self.learning_history.append(LearningEvent(
            timestamp=time.time(),
            event_type="weight_increase" if score_delta > 0 else "weight_decrease",
            pattern_id=pattern_id,
            old_weight=current_weight,
            new_weight=new_weight,
            reason=f"feedback_score_{score_delta:.2f}"
        ))

        return new_weight

    def prune_constraints(
        self,
        min_score: Optional[float] = None
    ) -> int:
        """
        Remove low-scoring constraints.

        Args:
            min_score: Override minimum score

        Returns:
            Number of constraints removed
        """
        threshold = min_score if min_score is not None else self.min_score

        to_remove = [
            pattern_id for pattern_id, weight in self.constraints.items()
            if weight < threshold
        ]

        for pattern_id in to_remove:
            del self.constraints[pattern_id]
            if pattern_id in self.constraint_metadata:
                del self.constraint_metadata[pattern_id]

            self.learning_history.append(LearningEvent(
                timestamp=time.time(),
                event_type="constraint_removed",
                pattern_id=pattern_id,
                old_weight=self.constraints.get(pattern_id, 0.0),
                new_weight=0.0,
                reason=f"weight_below_{threshold}"
            ))

        removed_count = len(to_remove)
        self.stats["constraints_removed"] += removed_count

        # Also enforce max constraints limit
        if len(self.constraints) > self.max_constraints:
            # Remove lowest-weighted constraints
            sorted_constraints = sorted(
                self.constraints.items(),
                key=lambda x: x[1]
            )
            excess = len(self.constraints) - self.max_constraints
            for pattern_id, _ in sorted_constraints[:excess]:
                del self.constraints[pattern_id]
                if pattern_id in self.constraint_metadata:
                    del self.constraint_metadata[pattern_id]
                removed_count += 1

        return removed_count

    def decay_weights(self) -> None:
        """Apply periodic decay to all weights."""
        for pattern_id in list(self.constraints.keys()):
            current_weight = self.constraints[pattern_id]
            new_weight = current_weight * (1.0 - self.decay_rate)

            if new_weight < self.min_score:
                del self.constraints[pattern_id]
                if pattern_id in self.constraint_metadata:
                    del self.constraint_metadata[pattern_id]
                self.stats["constraints_removed"] += 1
            else:
                self.constraints[pattern_id] = new_weight

    def get_learning_stats(self) -> dict[str, Any]:
        """
        Get learning statistics.

        Returns:
            Dictionary with stats
        """
        return {
            **self.stats,
            "total_constraints": len(self.constraints),
            "learning_history_size": len(self.learning_history),
            "avg_constraint_weight": (
                sum(self.constraints.values()) / len(self.constraints)
                if self.constraints else 0.0
            ),
        }


__all__ = [
    "ConstraintLearningSystem",
    "ConstraintRefinement",
    "Feedback",
    "GenerationResult",
    "ValidationResult",
    "RepairResult",
    "LearningEvent",
]
