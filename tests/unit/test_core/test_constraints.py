"""
Unit tests for constraint abstractions.
"""

import pytest
from maze.core.constraints import (
    TokenMask,
    GenerationState,
    Constraint,
    SyntacticConstraint,
    TypeConstraint,
    SemanticConstraint,
    ContextualConstraint,
    ConstraintSet,
    ConstraintLevel
)
from maze.core.types import Type, TypeContext, FunctionSignature, TypeParameter


class TestTokenMask:
    """Test TokenMask operations."""

    def test_token_mask_creation(self):
        """Test creating token masks."""
        mask = TokenMask(allowed_tokens={1, 2, 3})
        assert mask.allowed_tokens == {1, 2, 3}
        assert mask.forbidden_tokens is None

    def test_is_allowed(self):
        """Test token allowed checking."""
        mask = TokenMask(allowed_tokens={1, 2, 3})
        assert mask.is_allowed(1)
        assert mask.is_allowed(2)
        assert not mask.is_allowed(4)

    def test_is_allowed_with_forbidden(self):
        """Test token checking with forbidden tokens."""
        mask = TokenMask(forbidden_tokens={1, 2})
        assert not mask.is_allowed(1)
        assert not mask.is_allowed(2)
        assert mask.is_allowed(3)

    def test_merge_allowed_tokens(self):
        """Test merging allowed token sets."""
        mask1 = TokenMask(allowed_tokens={1, 2, 3, 4})
        mask2 = TokenMask(allowed_tokens={3, 4, 5, 6})
        merged = mask1.merge(mask2)

        # Should be intersection
        assert merged.allowed_tokens == {3, 4}

    def test_merge_forbidden_tokens(self):
        """Test merging forbidden token sets."""
        mask1 = TokenMask(forbidden_tokens={1, 2})
        mask2 = TokenMask(forbidden_tokens={3, 4})
        merged = mask1.merge(mask2)

        # Should be union
        assert merged.forbidden_tokens == {1, 2, 3, 4}

    def test_merge_logit_bias(self):
        """Test merging logit biases."""
        mask1 = TokenMask(logit_bias={1: 0.5, 2: -0.5})
        mask2 = TokenMask(logit_bias={2: -1.0, 3: 0.8})
        merged = mask1.merge(mask2)

        # Later values override
        assert merged.logit_bias[1] == 0.5
        assert merged.logit_bias[2] == -1.0
        assert merged.logit_bias[3] == 0.8


class TestGenerationState:
    """Test GenerationState operations."""

    def test_state_creation(self, type_context):
        """Test creating generation state."""
        state = GenerationState(
            generated_text="function hello",
            context=type_context,
            current_position=14,
            tokens_generated=3,
            language="typescript"
        )

        assert state.generated_text == "function hello"
        assert state.current_position == 14
        assert state.tokens_generated == 3
        assert state.language == "typescript"

    def test_state_copy(self, type_context):
        """Test copying generation state."""
        original = GenerationState(
            generated_text="test",
            context=type_context,
            current_position=4,
            tokens_generated=1,
            language="typescript"
        )

        copy = original.copy()
        assert copy.generated_text == original.generated_text
        assert copy.current_position == original.current_position
        assert copy is not original


class TestSyntacticConstraint:
    """Test syntactic constraint evaluation."""

    def test_syntactic_constraint_creation(self):
        """Test creating syntactic constraint."""
        grammar = """
            ?start: statement
            statement: IDENT "=" expression ";"
            expression: NUMBER | STRING
            IDENT: /[a-zA-Z_][a-zA-Z0-9_]*/
            NUMBER: /[0-9]+/
            STRING: /"[^"]*"/
            %ignore /\\s+/
        """

        constraint = SyntacticConstraint(grammar=grammar, language="typescript")
        assert constraint.level == ConstraintLevel.SYNTACTIC
        assert constraint.language == "typescript"
        assert constraint.grammar == grammar

    def test_syntactic_constraint_with_weight(self):
        """Test constraint with custom weight."""
        grammar = "?start: statement"
        # Weight is set in parent Constraint class, not in SyntacticConstraint
        constraint = SyntacticConstraint(grammar=grammar, language="python")
        # SyntacticConstraint defaults to SYNTACTIC level with weight 1.0
        assert constraint.weight == 1.0


class TestTypeConstraint:
    """Test type constraint evaluation."""

    def test_type_constraint_creation(self, type_context):
        """Test creating type constraint."""
        constraint = TypeConstraint(
            expected_type=Type("string"),
            context=type_context,
            strict=True
        )

        assert constraint.level == ConstraintLevel.TYPE
        assert constraint.expected_type == Type("string")
        assert constraint.strict

    def test_type_constraint_with_generic(self, type_context):
        """Test type constraint with generic type."""
        array_of_numbers = Type("Array", (Type("number"),))
        constraint = TypeConstraint(
            expected_type=array_of_numbers,
            context=type_context,
            strict=False
        )

        assert constraint.expected_type.name == "Array"
        assert len(constraint.expected_type.parameters) == 1
        assert constraint.expected_type.parameters[0].name == "number"


class TestSemanticConstraint:
    """Test semantic constraint evaluation."""

    def test_semantic_constraint_creation(self):
        """Test creating semantic constraint."""
        # SemanticConstraint takes specification string, not property_name
        constraint = SemanticConstraint(
            specification="validates_email: must validate email addresses correctly"
        )

        # Add test cases via method (takes input and expected_output as separate args)
        constraint.add_test_case("test@example.com", True)
        constraint.add_test_case("invalid", False)

        assert constraint.level == ConstraintLevel.SEMANTIC
        assert constraint.specification == "validates_email: must validate email addresses correctly"
        assert len(constraint.test_cases) == 2


class TestContextualConstraint:
    """Test contextual constraint evaluation."""

    def test_contextual_constraint_creation(self):
        """Test creating contextual constraint."""
        # ContextualConstraint takes weight, not patterns
        constraint = ContextualConstraint(weight=0.5)

        # Add patterns via method
        constraint.add_pattern("prefer async/await over promises")
        constraint.add_pattern("use const for immutable values")

        assert constraint.level == ConstraintLevel.CONTEXTUAL
        assert constraint.weight == 0.5
        assert len(constraint.patterns) == 2


class TestConstraintSet:
    """Test constraint set operations."""

    def test_constraint_set_creation(self):
        """Test creating empty constraint set."""
        constraints = ConstraintSet()
        assert len(constraints.syntactic) == 0
        assert len(constraints.type_based) == 0
        assert len(constraints.semantic) == 0
        assert len(constraints.contextual) == 0

    def test_add_constraint(self, syntactic_constraint):
        """Test adding constraint to set."""
        constraints = ConstraintSet()
        constraints.add(syntactic_constraint)

        assert len(constraints.syntactic) == 1
        assert constraints.syntactic[0] == syntactic_constraint

    def test_add_multiple_constraints(self, syntactic_constraint, type_constraint):
        """Test adding multiple constraints."""
        constraints = ConstraintSet()
        constraints.add(syntactic_constraint)
        constraints.add(type_constraint)

        assert len(constraints.syntactic) == 1
        assert len(constraints.type_based) == 1

    def test_hierarchical_composition(self):
        """Test hierarchical constraint composition."""
        # Create all 4 levels
        syntactic = SyntacticConstraint(grammar="?start: expr", language="python")
        type_c = TypeConstraint(expected_type=Type("int"), context=TypeContext("python"))
        semantic = SemanticConstraint(specification="test specification")
        contextual = ContextualConstraint(weight=0.5)

        # Add to set
        constraints = ConstraintSet()
        constraints.add(syntactic)
        constraints.add(type_c)
        constraints.add(semantic)
        constraints.add(contextual)

        # Verify hierarchy
        assert len(constraints.syntactic) == 1
        assert len(constraints.type_based) == 1
        assert len(constraints.semantic) == 1
        assert len(constraints.contextual) == 1

    def test_get_all_constraints(self):
        """Test retrieving all constraints."""
        constraints = ConstraintSet()
        constraints.add(SyntacticConstraint(grammar="?start: e", language="ts"))
        constraints.add(TypeConstraint(expected_type=Type("string"), context=TypeContext("ts")))

        all_constraints = constraints.get_all()
        assert len(all_constraints) == 2

    def test_constraint_set_from_list(self):
        """Test creating constraint set from list."""
        constraint_list = [
            SyntacticConstraint(grammar="?start: e", language="python"),
            TypeConstraint(expected_type=Type("int"), context=TypeContext("python"))
        ]

        constraints = ConstraintSet.from_list(constraint_list)
        assert len(constraints.syntactic) == 1
        assert len(constraints.type_based) == 1
