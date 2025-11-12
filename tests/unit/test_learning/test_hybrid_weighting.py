"""
Tests for hybrid constraint weighting.
"""


import pytest

from maze.learning.hybrid_weighting import (
    ConstraintSet,
    GenerationState,
    HybridConstraintWeighter,
    TokenWeights,
    WeightedConstraintSet,
)


class TestHybridConstraintWeighter:
    """Test HybridConstraintWeighter class."""

    @pytest.fixture
    def weighter(self):
        """Create hybrid constraint weighter."""
        return HybridConstraintWeighter(default_temperature=0.5)

    @pytest.fixture
    def vocab(self):
        """Create sample vocabulary."""
        return ["def", "class", "if", "else", "return", "pass", "for", "while"]

    @pytest.fixture
    def generation_state(self, vocab):
        """Create generation state."""
        return GenerationState(vocabulary=vocab)

    def test_init(self, weighter):
        """Test initialization."""
        assert weighter.default_temperature == 0.5
        assert len(weighter.constraint_registry) == 0

    def test_init_custom_temperature(self):
        """Test initialization with custom temperature."""
        weighter = HybridConstraintWeighter(default_temperature=0.8)
        assert weighter.default_temperature == 0.8

    def test_combine_constraints_empty(self, weighter):
        """Test combining empty constraint sets."""
        hard = ConstraintSet(constraints=[])
        soft = ConstraintSet(constraints=[])

        result = weighter.combine_constraints(hard, soft)

        assert isinstance(result, WeightedConstraintSet)
        assert result.hard_constraints == hard
        assert len(result.soft_constraints) == 0
        assert result.temperature == 0.5

    def test_combine_constraints_with_temperature(self, weighter):
        """Test combining constraints with custom temperature."""
        hard = ConstraintSet(constraints=[])
        soft = ConstraintSet(constraints=[])

        result = weighter.combine_constraints(hard, soft, temperature=0.8)

        assert result.temperature == 0.8

    def test_combine_constraints_clamps_temperature(self, weighter):
        """Test that temperature is clamped to [0, 1]."""
        hard = ConstraintSet(constraints=[])
        soft = ConstraintSet(constraints=[])

        result1 = weighter.combine_constraints(hard, soft, temperature=-0.5)
        assert result1.temperature == 0.0

        result2 = weighter.combine_constraints(hard, soft, temperature=1.5)
        assert result2.temperature == 1.0

    def test_compute_token_weights_uniform(self, weighter, generation_state):
        """Test computing uniform token weights."""
        weighted = WeightedConstraintSet(
            hard_constraints=ConstraintSet([]), soft_constraints={}, temperature=1.0
        )

        weights = weighter.compute_token_weights(weighted, generation_state)

        assert isinstance(weights, TokenWeights)
        assert len(weights.weights) == len(generation_state.vocabulary)
        assert len(weights.hard_masked) == len(generation_state.vocabulary)

        # All weights should be equal (uniform)
        assert all(abs(w - weights.weights[0]) < 1e-6 for w in weights.weights)

    def test_apply_temperature_zero(self, weighter):
        """Test temperature = 0 (select only top tokens)."""
        weights = TokenWeights(
            token_ids=[0, 1, 2, 3],
            weights=[0.4, 0.3, 0.2, 0.1],
            hard_masked=[False, False, False, False],
        )

        scaled = weighter.apply_temperature(weights, temperature=0.0)

        # Only maximum weight should remain
        assert scaled.weights[0] > 0  # Highest weight
        assert all(w == 0 for w in scaled.weights[1:])  # Others zero

    def test_apply_temperature_one(self, weighter):
        """Test temperature = 1.0 (neutral, no change)."""
        original_weights = [0.4, 0.3, 0.2, 0.1]
        weights = TokenWeights(
            token_ids=[0, 1, 2, 3],
            weights=original_weights.copy(),
            hard_masked=[False, False, False, False],
        )

        scaled = weighter.apply_temperature(weights, temperature=1.0)

        # Weights should be approximately same after normalization
        total = sum(original_weights)
        expected = [w / total for w in original_weights]

        for i, (actual, exp) in enumerate(zip(scaled.weights, expected)):
            assert abs(actual - exp) < 1e-6

    def test_apply_temperature_high(self, weighter):
        """Test high temperature (flattens distribution)."""
        weights = TokenWeights(
            token_ids=[0, 1, 2, 3],
            weights=[0.8, 0.1, 0.05, 0.05],
            hard_masked=[False, False, False, False],
        )

        scaled = weighter.apply_temperature(weights, temperature=2.0)

        # Distribution should be flatter (less extreme)
        assert scaled.weights[0] < 0.8  # Highest reduced
        assert scaled.weights[1] > 0.1  # Lowest increased

    def test_apply_temperature_respects_hard_mask(self, weighter):
        """Test that temperature respects hard masks."""
        weights = TokenWeights(
            token_ids=[0, 1, 2, 3],
            weights=[0.4, 0.3, 0.2, 0.1],
            hard_masked=[False, True, False, True],
        )

        scaled = weighter.apply_temperature(weights, temperature=0.5)

        # Masked tokens should remain zero
        assert scaled.weights[1] == 0.0
        assert scaled.weights[3] == 0.0
        assert scaled.hard_masked[1] is True
        assert scaled.hard_masked[3] is True

    def test_constraint_to_id_deterministic(self, weighter):
        """Test that constraint ID generation is deterministic."""
        constraint1 = {"type": "syntax", "rule": "no_globals"}
        constraint2 = {"type": "syntax", "rule": "no_globals"}

        id1 = weighter._constraint_to_id(constraint1)
        id2 = weighter._constraint_to_id(constraint2)

        assert id1 == id2

    def test_constraint_to_id_unique(self, weighter):
        """Test that different constraints get different IDs."""
        constraint1 = {"type": "syntax", "rule": "no_globals"}
        constraint2 = {"type": "syntax", "rule": "no_locals"}

        id1 = weighter._constraint_to_id(constraint1)
        id2 = weighter._constraint_to_id(constraint2)

        assert id1 != id2

    def test_register_constraint(self, weighter):
        """Test constraint registration."""
        constraint = {"type": "syntax", "rule": "test"}
        constraint_id = "test-id"

        weighter.register_constraint(constraint_id, constraint)

        assert constraint_id in weighter.constraint_registry
        assert weighter.constraint_registry[constraint_id] == constraint

    def test_id_to_constraint(self, weighter):
        """Test retrieving constraint by ID."""
        constraint = {"type": "syntax", "rule": "test"}
        constraint_id = "test-id"
        weighter.register_constraint(constraint_id, constraint)

        retrieved = weighter._id_to_constraint(constraint_id)

        assert retrieved == constraint

    def test_id_to_constraint_not_found(self, weighter):
        """Test retrieving non-existent constraint."""
        result = weighter._id_to_constraint("nonexistent")
        assert result is None

    def test_get_allowed_tokens_default(self, weighter, generation_state):
        """Test default allowed tokens (all)."""
        constraint = {"type": "test"}
        allowed = weighter._get_allowed_tokens(constraint, generation_state)

        assert len(allowed) == len(generation_state.vocabulary)

    def test_get_preferred_tokens_default(self, weighter, generation_state):
        """Test default preferred tokens (none)."""
        constraint = {"type": "test"}
        preferred = weighter._get_preferred_tokens(constraint, generation_state)

        assert len(preferred) == 0

    def test_get_effective_weight(self, weighter):
        """Test getting effective weight for token."""
        weights = TokenWeights(
            token_ids=[0, 1, 2], weights=[0.5, 0.3, 0.2], hard_masked=[False, False, False]
        )

        assert weighter.get_effective_weight(0, weights) == 0.5
        assert weighter.get_effective_weight(1, weights) == 0.3
        assert weighter.get_effective_weight(2, weights) == 0.2

    def test_get_effective_weight_out_of_bounds(self, weighter):
        """Test effective weight for out-of-bounds token."""
        weights = TokenWeights(
            token_ids=[0, 1, 2], weights=[0.5, 0.3, 0.2], hard_masked=[False, False, False]
        )

        assert weighter.get_effective_weight(-1, weights) == 0.0
        assert weighter.get_effective_weight(10, weights) == 0.0

    def test_merge_token_weights_equal(self, weighter):
        """Test merging weights with equal mixing."""
        weights1 = TokenWeights(
            token_ids=[0, 1, 2], weights=[0.6, 0.3, 0.1], hard_masked=[False, False, False]
        )
        weights2 = TokenWeights(
            token_ids=[0, 1, 2], weights=[0.2, 0.5, 0.3], hard_masked=[False, False, False]
        )

        merged = weighter.merge_token_weights(weights1, weights2, alpha=0.5)

        # Should be average of both
        expected = [0.4, 0.4, 0.2]
        for actual, exp in zip(merged.weights, expected):
            assert abs(actual - exp) < 1e-6

    def test_merge_token_weights_alpha_zero(self, weighter):
        """Test merging weights with alpha=0 (all weights2)."""
        weights1 = TokenWeights(
            token_ids=[0, 1, 2], weights=[0.6, 0.3, 0.1], hard_masked=[False, False, False]
        )
        weights2 = TokenWeights(
            token_ids=[0, 1, 2], weights=[0.2, 0.5, 0.3], hard_masked=[False, False, False]
        )

        merged = weighter.merge_token_weights(weights1, weights2, alpha=0.0)

        # Should match weights2
        for actual, exp in zip(merged.weights, weights2.weights):
            assert abs(actual - exp) < 1e-6

    def test_merge_token_weights_alpha_one(self, weighter):
        """Test merging weights with alpha=1 (all weights1)."""
        weights1 = TokenWeights(
            token_ids=[0, 1, 2], weights=[0.6, 0.3, 0.1], hard_masked=[False, False, False]
        )
        weights2 = TokenWeights(
            token_ids=[0, 1, 2], weights=[0.2, 0.5, 0.3], hard_masked=[False, False, False]
        )

        merged = weighter.merge_token_weights(weights1, weights2, alpha=1.0)

        # Should match weights1
        for actual, exp in zip(merged.weights, weights1.weights):
            assert abs(actual - exp) < 1e-6

    def test_merge_token_weights_preserves_masks(self, weighter):
        """Test that merging preserves hard masks."""
        weights1 = TokenWeights(
            token_ids=[0, 1, 2], weights=[0.6, 0.3, 0.1], hard_masked=[False, True, False]
        )
        weights2 = TokenWeights(
            token_ids=[0, 1, 2], weights=[0.2, 0.5, 0.3], hard_masked=[False, False, True]
        )

        merged = weighter.merge_token_weights(weights1, weights2, alpha=0.5)

        # Masks should be OR'd
        assert merged.hard_masked == [False, True, True]

    def test_compute_token_weights_normalization(self, weighter, generation_state):
        """Test that computed weights are normalized."""
        weighted = WeightedConstraintSet(
            hard_constraints=ConstraintSet([]), soft_constraints={}, temperature=1.0
        )

        weights = weighter.compute_token_weights(weighted, generation_state)

        # Sum of non-masked weights should be approximately 1.0
        total = sum(w for w, masked in zip(weights.weights, weights.hard_masked) if not masked)
        assert abs(total - 1.0) < 1e-6

    def test_temperature_effects_on_distribution(self, weighter):
        """Test temperature effects on distribution shape."""
        weights = TokenWeights(
            token_ids=[0, 1, 2, 3, 4], weights=[0.5, 0.2, 0.15, 0.1, 0.05], hard_masked=[False] * 5
        )

        # Low temperature should sharpen
        low_temp = weighter.apply_temperature(weights, temperature=0.3)

        # High temperature should flatten
        high_temp = weighter.apply_temperature(weights, temperature=2.0)

        # Low temp should have higher max/min ratio
        low_ratio = (
            low_temp.weights[0] / low_temp.weights[-1] if low_temp.weights[-1] > 0 else float("inf")
        )
        high_ratio = (
            high_temp.weights[0] / high_temp.weights[-1]
            if high_temp.weights[-1] > 0
            else float("inf")
        )

        assert low_ratio > high_ratio

    def test_soft_constraint_extraction(self, weighter):
        """Test extracting soft constraint weights."""

        class MockConstraint:
            def __init__(self, weight):
                self.weight = weight

        soft = ConstraintSet(
            constraints=[
                MockConstraint(0.8),
                MockConstraint(0.5),
                MockConstraint(0.3),
            ]
        )

        weighted = weighter.combine_constraints(ConstraintSet([]), soft, temperature=0.5)

        assert len(weighted.soft_constraints) == 3

    def test_empty_vocabulary(self, weighter):
        """Test handling empty vocabulary."""
        state = GenerationState(vocabulary=[])
        weighted = WeightedConstraintSet(
            hard_constraints=ConstraintSet([]), soft_constraints={}, temperature=1.0
        )

        weights = weighter.compute_token_weights(weighted, state)

        assert len(weights.weights) == 0
        assert len(weights.hard_masked) == 0

    def test_single_token_vocabulary(self, weighter):
        """Test with single token vocabulary."""
        state = GenerationState(vocabulary=["token"])
        weighted = WeightedConstraintSet(
            hard_constraints=ConstraintSet([]), soft_constraints={}, temperature=1.0
        )

        weights = weighter.compute_token_weights(weighted, state)

        assert len(weights.weights) == 1
        assert weights.weights[0] == 1.0  # Single token gets full weight

    def test_all_tokens_masked(self, weighter):
        """Test behavior when all tokens are masked."""
        weights = TokenWeights(
            token_ids=[0, 1, 2], weights=[0.0, 0.0, 0.0], hard_masked=[True, True, True]
        )

        scaled = weighter.apply_temperature(weights, temperature=0.5)

        # All should remain zero
        assert all(w == 0.0 for w in scaled.weights)
        assert all(m for m in scaled.hard_masked)
