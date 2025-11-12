"""
Hybrid constraint weighting for adaptive code generation.

Combines hard and soft constraints with temperature control.
"""

import math
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ConstraintSet:
    """Set of constraints."""

    constraints: list[Any] = field(default_factory=list)


@dataclass
class WeightedConstraintSet:
    """Constraint set with weights."""

    hard_constraints: ConstraintSet  # Binary (always enforced)
    soft_constraints: dict[str, float]  # Constraint ID -> weight
    temperature: float  # 0-1


@dataclass
class GenerationState:
    """Current generation state."""

    vocabulary: list[str]
    current_tokens: list[int] = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=dict)


@dataclass
class TokenWeights:
    """Per-token weights for generation."""

    token_ids: list[int]
    weights: list[float]  # 0-1
    hard_masked: list[bool]  # Hard constraint mask


class HybridConstraintWeighter:
    """
    Combine hard and soft constraints.

    Hard constraints: Binary enforcement (must satisfy)
    Soft constraints: Weighted preferences (boost probabilities)
    Temperature: Control between strict (0) and creative (1+)
    """

    def __init__(self, default_temperature: float = 0.5):
        """
        Initialize hybrid constraint weighter.

        Args:
            default_temperature: Default temperature (0-1)
        """
        self.default_temperature = default_temperature
        self.constraint_registry: dict[str, Any] = {}

    def combine_constraints(
        self, hard: ConstraintSet, soft: ConstraintSet, temperature: float | None = None
    ) -> WeightedConstraintSet:
        """
        Combine hard and soft constraints.

        Args:
            hard: Hard constraints (always enforced)
            soft: Soft constraints (preferences)
            temperature: Temperature (0-1, None = use default)

        Returns:
            Weighted constraint set
        """
        temp = temperature if temperature is not None else self.default_temperature
        temp = max(0.0, min(1.0, temp))  # Clamp to [0, 1]

        # Extract soft constraint weights
        soft_weights = {}
        for constraint in soft.constraints:
            constraint_id = self._constraint_to_id(constraint)
            weight = getattr(constraint, "weight", 0.5)
            soft_weights[constraint_id] = weight

        return WeightedConstraintSet(
            hard_constraints=hard, soft_constraints=soft_weights, temperature=temp
        )

    def compute_token_weights(
        self, weighted_constraints: WeightedConstraintSet, current_state: GenerationState
    ) -> TokenWeights:
        """
        Compute per-token weights.

        Args:
            weighted_constraints: Weighted constraints
            current_state: Current generation state

        Returns:
            Token weights
        """
        vocab_size = len(current_state.vocabulary)

        # Start with uniform weights
        token_weights = [1.0] * vocab_size
        hard_masked = [False] * vocab_size

        # Apply hard constraints (binary mask)
        for constraint in weighted_constraints.hard_constraints.constraints:
            allowed_tokens = self._get_allowed_tokens(constraint, current_state)
            for token_id in range(vocab_size):
                if token_id not in allowed_tokens:
                    token_weights[token_id] = 0.0
                    hard_masked[token_id] = True

        # Apply soft constraints (weight adjustments)
        for constraint_id, weight in weighted_constraints.soft_constraints.items():
            constraint = self._id_to_constraint(constraint_id)
            if constraint:
                preferred_tokens = self._get_preferred_tokens(constraint, current_state)

                for token_id in preferred_tokens:
                    if token_id < vocab_size and not hard_masked[token_id]:
                        # Boost weight for preferred tokens
                        token_weights[token_id] *= 1.0 + weight

        # Normalize weights
        total_weight = sum(w for w, masked in zip(token_weights, hard_masked) if not masked)
        if total_weight > 0:
            token_weights = [
                w / total_weight if not masked else 0.0
                for w, masked in zip(token_weights, hard_masked)
            ]

        # Create token weights object
        token_weights_obj = TokenWeights(
            token_ids=list(range(vocab_size)), weights=token_weights, hard_masked=hard_masked
        )

        # Apply temperature
        if weighted_constraints.temperature != 1.0:
            token_weights_obj = self.apply_temperature(
                token_weights_obj, weighted_constraints.temperature
            )

        return token_weights_obj

    def apply_temperature(self, weights: TokenWeights, temperature: float) -> TokenWeights:
        """
        Apply temperature scaling to weights.

        Temperature effects:
        - temp = 0: Very strict (select only top tokens)
        - temp = 0.5: Moderate (sharpen distribution)
        - temp = 1.0: Neutral (no change)
        - temp > 1.0: Creative (flatten distribution)

        Args:
            weights: Token weights
            temperature: Temperature (0-1+)

        Returns:
            Scaled weights
        """
        if temperature == 0:
            # Select top tokens only
            max_weight = max(weights.weights) if weights.weights else 0.0
            scaled_weights = [
                w if w == max_weight and not masked else 0.0
                for w, masked in zip(weights.weights, weights.hard_masked)
            ]
        else:
            # Softmax-style temperature scaling
            scaled_weights = []
            for w, masked in zip(weights.weights, weights.hard_masked):
                if masked:
                    scaled_weights.append(0.0)
                else:
                    # Scale by temperature (higher temp = flatter)
                    if w > 0:
                        scaled = math.exp(math.log(w + 1e-10) / temperature)
                    else:
                        scaled = 0.0
                    scaled_weights.append(scaled)

            # Renormalize
            total = sum(scaled_weights)
            if total > 0:
                scaled_weights = [w / total for w in scaled_weights]

        return TokenWeights(
            token_ids=weights.token_ids, weights=scaled_weights, hard_masked=weights.hard_masked
        )

    def _constraint_to_id(self, constraint: Any) -> str:
        """Convert constraint to unique ID."""
        import hashlib

        constraint_str = str(constraint)
        return f"con-{hashlib.md5(constraint_str.encode()).hexdigest()[:8]}"

    def _id_to_constraint(self, constraint_id: str) -> Any | None:
        """Get constraint from ID."""
        return self.constraint_registry.get(constraint_id)

    def _get_allowed_tokens(self, constraint: Any, state: GenerationState) -> set[int]:
        """
        Get tokens allowed by hard constraint.

        Args:
            constraint: Hard constraint
            state: Generation state

        Returns:
            Set of allowed token IDs
        """
        # Default: allow all tokens
        # In practice, this would parse the constraint and determine allowed tokens
        return set(range(len(state.vocabulary)))

    def _get_preferred_tokens(self, constraint: Any, state: GenerationState) -> set[int]:
        """
        Get tokens preferred by soft constraint.

        Args:
            constraint: Soft constraint
            state: Generation state

        Returns:
            Set of preferred token IDs
        """
        # Default: no preferences
        # In practice, this would extract preferred tokens from the constraint
        return set()

    def register_constraint(self, constraint_id: str, constraint: Any) -> None:
        """
        Register a constraint for later lookup.

        Args:
            constraint_id: Constraint identifier
            constraint: Constraint object
        """
        self.constraint_registry[constraint_id] = constraint

    def get_effective_weight(self, token_id: int, weights: TokenWeights) -> float:
        """
        Get effective weight for a token.

        Args:
            token_id: Token identifier
            weights: Token weights

        Returns:
            Effective weight (0-1)
        """
        if token_id < 0 or token_id >= len(weights.weights):
            return 0.0
        return weights.weights[token_id]

    def merge_token_weights(
        self, weights1: TokenWeights, weights2: TokenWeights, alpha: float = 0.5
    ) -> TokenWeights:
        """
        Merge two token weight sets.

        Args:
            weights1: First weight set
            weights2: Second weight set
            alpha: Mixing coefficient (0-1)

        Returns:
            Merged weights
        """
        assert len(weights1.weights) == len(weights2.weights), "Weight sets must have same size"

        merged_weights = [
            alpha * w1 + (1 - alpha) * w2 for w1, w2 in zip(weights1.weights, weights2.weights)
        ]

        merged_masked = [m1 or m2 for m1, m2 in zip(weights1.hard_masked, weights2.hard_masked)]

        return TokenWeights(
            token_ids=weights1.token_ids, weights=merged_weights, hard_masked=merged_masked
        )


__all__ = [
    "HybridConstraintWeighter",
    "WeightedConstraintSet",
    "TokenWeights",
    "ConstraintSet",
    "GenerationState",
]
