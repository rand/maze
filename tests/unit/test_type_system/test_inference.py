"""
Tests for type inference engine.
"""

from maze.core.types import ClassType, FunctionSignature, Type, TypeContext
from maze.type_system.inference import (
    InferenceResult,
    TypeConstraint,
    TypeInferenceEngine,
)


class TestTypeInference:
    """Test type inference engine."""

    def test_infer_literal_number(self):
        """Test inferring number literal type."""
        engine = TypeInferenceEngine()
        context = TypeContext()

        expr = {"kind": "literal", "value": 42}
        result = engine.infer_expression(expr, context)

        assert result.inferred_type == Type("number")
        assert result.confidence == 1.0

    def test_infer_literal_string(self):
        """Test inferring string literal type."""
        engine = TypeInferenceEngine()
        context = TypeContext()

        expr = {"kind": "literal", "value": "hello"}
        result = engine.infer_expression(expr, context)

        assert result.inferred_type == Type("string")
        assert result.confidence == 1.0

    def test_infer_literal_boolean(self):
        """Test inferring boolean literal type."""
        engine = TypeInferenceEngine()
        context = TypeContext()

        expr_true = {"kind": "literal", "value": True}
        result_true = engine.infer_expression(expr_true, context)

        assert result_true.inferred_type == Type("boolean")

        expr_false = {"kind": "literal", "value": False}
        result_false = engine.infer_expression(expr_false, context)

        assert result_false.inferred_type == Type("boolean")

    def test_infer_variable_from_context(self):
        """Test inferring variable type from context."""
        engine = TypeInferenceEngine()
        context = TypeContext(
            variables={
                "x": Type("number"),
                "name": Type("string"),
            }
        )

        expr_x = {"kind": "identifier", "name": "x"}
        result_x = engine.infer_expression(expr_x, context)

        assert result_x.inferred_type == Type("number")
        assert result_x.confidence == 1.0

        expr_name = {"kind": "identifier", "name": "name"}
        result_name = engine.infer_expression(expr_name, context)

        assert result_name.inferred_type == Type("string")

    def test_infer_unknown_identifier(self):
        """Test inferring unknown identifier returns unknown type."""
        engine = TypeInferenceEngine()
        context = TypeContext()

        expr = {"kind": "identifier", "name": "unknown_var"}
        result = engine.infer_expression(expr, context)

        assert result.inferred_type == Type("unknown")
        assert result.confidence == 0.0

    def test_infer_function_call(self):
        """Test inferring function call return type."""
        engine = TypeInferenceEngine()

        # Create context with function
        get_name_sig = FunctionSignature(name="getName", parameters=[], return_type=Type("string"))

        context = TypeContext(functions={"getName": get_name_sig})

        # Call expression
        expr = {
            "kind": "call",
            "callee": {"kind": "identifier", "name": "getName"},
            "arguments": [],
        }

        result = engine.infer_expression(expr, context)

        # Should infer string return type
        assert result.inferred_type == Type("string")

    def test_infer_property_access(self):
        """Test inferring property access type."""
        engine = TypeInferenceEngine()

        # Create class type
        person_class = ClassType(
            name="Person",
            properties={
                "name": Type("string"),
                "age": Type("number"),
            },
            methods={},
        )

        context = TypeContext(
            variables={"person": Type("Person")}, classes={"Person": person_class}
        )

        # Property access: person.name
        expr = {
            "kind": "property",
            "object": {"kind": "identifier", "name": "person"},
            "property": "name",
        }

        result = engine.infer_expression(expr, context)

        assert result.inferred_type == Type("string")

    def test_infer_array_literal(self):
        """Test inferring array literal type."""
        engine = TypeInferenceEngine()
        context = TypeContext()

        # Array of numbers
        expr = {
            "kind": "array",
            "elements": [
                {"kind": "literal", "value": 1},
                {"kind": "literal", "value": 2},
                {"kind": "literal", "value": 3},
            ],
        }

        result = engine.infer_expression(expr, context)

        assert result.inferred_type == Type("Array", (Type("number"),))

    def test_infer_empty_array(self):
        """Test inferring empty array type."""
        engine = TypeInferenceEngine()
        context = TypeContext()

        expr = {"kind": "array", "elements": []}

        result = engine.infer_expression(expr, context)

        assert result.inferred_type == Type("Array", (Type("unknown"),))
        assert result.confidence == 0.5

    def test_infer_object_literal(self):
        """Test inferring object literal type."""
        engine = TypeInferenceEngine()
        context = TypeContext()

        expr = {
            "kind": "object",
            "properties": [
                {"key": "name", "value": {"kind": "literal", "value": "Alice"}},
                {"key": "age", "value": {"kind": "literal", "value": 30}},
            ],
        }

        result = engine.infer_expression(expr, context)

        # Returns generic object type
        assert result.inferred_type == Type("object")

    def test_check_valid_type(self):
        """Test checking expression has expected type."""
        engine = TypeInferenceEngine()
        context = TypeContext()

        expr = {"kind": "literal", "value": 42}

        assert engine.check_expression(expr, Type("number"), context) is True

    def test_check_invalid_type(self):
        """Test checking expression with wrong expected type."""
        engine = TypeInferenceEngine()
        context = TypeContext()

        expr = {"kind": "literal", "value": 42}

        assert engine.check_expression(expr, Type("string"), context) is False

    def test_unify_same_types(self):
        """Test unifying identical types."""
        engine = TypeInferenceEngine()

        subst = engine.unify(Type("number"), Type("number"))

        assert subst is not None
        assert subst == {}

    def test_unify_generic_types(self):
        """Test unifying generic types."""
        engine = TypeInferenceEngine()

        # Unify Array<T> with Array<number>
        generic = Type("Array", (Type("T"),))
        concrete = Type("Array", (Type("number"),))

        subst = engine.unify(generic, concrete)

        assert subst is not None
        assert subst == {"T": Type("number")}

    def test_unify_incompatible_types(self):
        """Test unifying incompatible types."""
        engine = TypeInferenceEngine()

        subst = engine.unify(Type("number"), Type("string"))

        assert subst is None

    def test_forward_inference(self):
        """Test forward (bottom-up) inference."""
        engine = TypeInferenceEngine()
        context = TypeContext(variables={"x": Type("number")})

        expr = {"kind": "identifier", "name": "x"}

        inferred = engine.infer_forward(expr, context)

        assert inferred == Type("number")

    def test_backward_inference(self):
        """Test backward (top-down) inference with type refinement."""
        engine = TypeInferenceEngine()

        # Variable x has nullable string type
        context = TypeContext(variables={"x": Type("string", nullable=True)})

        expr = {"kind": "identifier", "name": "x"}

        # But it's used in a context requiring non-null string
        refined = engine.infer_backward(expr, Type("string"), context)

        # Should refine to non-nullable
        assert refined == Type("string")
        assert refined.nullable is False

    def test_inference_caching(self):
        """Test that inference results are cached."""
        engine = TypeInferenceEngine()
        context = TypeContext(variables={"x": Type("number")})

        expr = {"kind": "identifier", "name": "x"}

        # First inference
        result1 = engine.infer_expression(expr, context)

        # Second inference (should use cache)
        result2 = engine.infer_expression(expr, context)

        # Should be same object (cached)
        assert result1 is result2

    def test_apply_substitution(self):
        """Test applying type variable substitution."""
        engine = TypeInferenceEngine()

        # Type: Array<T>
        generic_type = Type("Array", (Type("T"),))

        # Substitution: T -> number
        subst = {"T": Type("number")}

        # Apply substitution
        concrete_type = engine.apply_substitution(generic_type, subst)

        assert concrete_type == Type("Array", (Type("number"),))

    def test_infer_function_expression(self):
        """Test inferring function expression type."""
        engine = TypeInferenceEngine()
        context = TypeContext()

        expr = {
            "kind": "function",
            "parameters": [
                {"name": "x", "type": "number"},
                {"name": "y", "type": "number"},
            ],
            "returnType": "number",
        }

        result = engine.infer_expression(expr, context)

        # Should be function(number, number, number) - params + return
        expected = Type("function", (Type("number"), Type("number"), Type("number")))
        assert result.inferred_type == expected


class TestTypeConstraint:
    """Test type constraints."""

    def test_constraint_creation(self):
        """Test creating type constraints."""
        constraint = TypeConstraint(variable="T", constraint_type="subtype", bound=Type("number"))

        assert constraint.variable == "T"
        assert constraint.constraint_type == "subtype"
        assert constraint.bound == Type("number")

    def test_constraint_string_representation(self):
        """Test constraint string representation."""
        subtype = TypeConstraint("T", "subtype", Type("number"))
        assert str(subtype) == "T <: number"

        supertype = TypeConstraint("T", "supertype", Type("string"))
        assert str(supertype) == "T :> string"

        equals = TypeConstraint("T", "equals", Type("boolean"))
        assert str(equals) == "T = boolean"


class TestInferenceResult:
    """Test inference results."""

    def test_result_creation(self):
        """Test creating inference result."""
        result = InferenceResult(inferred_type=Type("number"), constraints=[], confidence=1.0)

        assert result.inferred_type == Type("number")
        assert result.constraints == []
        assert result.confidence == 1.0

    def test_result_with_constraints(self):
        """Test result with type constraints."""
        constraints = [TypeConstraint("T", "subtype", Type("number"))]

        result = InferenceResult(inferred_type=Type("T"), constraints=constraints, confidence=0.9)

        assert len(result.constraints) == 1
        assert result.constraints[0].variable == "T"

    def test_result_string_representation(self):
        """Test result string representation."""
        result = InferenceResult(inferred_type=Type("number"), confidence=1.0)

        assert "number" in str(result)
        assert "1.00" in str(result)
