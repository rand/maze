"""
Type inference engine for the Maze type system.

Implements bidirectional type inference with forward and backward passes,
type unification, and constraint solving.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple, Literal
from enum import Enum

from maze.core.types import (
    Type, TypeContext, FunctionSignature, TypeParameter,
    ClassType, InterfaceType, PRIMITIVE_TYPES
)


@dataclass
class TypeConstraint:
    """
    Constraint on a type variable.

    Examples:
        - TypeConstraint("T", "subtype", Type("number"))  # T <: number
        - TypeConstraint("T", "supertype", Type("string"))  # T :> string
        - TypeConstraint("T", "equals", Type("boolean"))  # T = boolean
    """
    variable: str
    constraint_type: Literal["subtype", "supertype", "equals"]
    bound: Type

    def __str__(self) -> str:
        symbols = {
            "subtype": "<:",
            "supertype": ":>",
            "equals": "="
        }
        symbol = symbols[self.constraint_type]
        return f"{self.variable} {symbol} {self.bound}"


@dataclass
class InferenceResult:
    """
    Result of type inference.

    Contains the inferred type, any constraints on type variables,
    and a confidence score for the inference.
    """
    inferred_type: Type
    constraints: List[TypeConstraint] = field(default_factory=list)
    confidence: float = 1.0  # 0.0 = guess, 1.0 = certain

    def __str__(self) -> str:
        constraints_str = ""
        if self.constraints:
            constraints_str = f" with constraints [{', '.join(str(c) for c in self.constraints)}]"
        return f"{self.inferred_type}{constraints_str} (confidence: {self.confidence:.2f})"


class TypeInferenceEngine:
    """
    Bidirectional type inference engine.

    Implements type inference using a combination of:
    - Forward inference: infer types from context (bottom-up)
    - Backward inference: refine types from usage (top-down)
    - Unification: combine type information from multiple sources

    Performance target: <100μs per expression
    """

    def __init__(self):
        """Initialize the type inference engine."""
        self.inference_cache: Dict[int, InferenceResult] = {}

    def infer_expression(
        self,
        expr: Any,
        context: TypeContext
    ) -> InferenceResult:
        """
        Infer the type of an expression from context.

        Args:
            expr: Expression to infer type for (AST node or dict)
            context: Type context containing available symbols

        Returns:
            InferenceResult with inferred type and constraints

        Example:
            >>> engine = TypeInferenceEngine()
            >>> context = TypeContext(variables={"x": Type("number")})
            >>> result = engine.infer_expression({"kind": "identifier", "name": "x"}, context)
            >>> print(result.inferred_type)
            number
        """
        # Cache key based on expression structure
        cache_key = self._cache_key(expr, context)
        if cache_key in self.inference_cache:
            return self.inference_cache[cache_key]

        # Handle different expression kinds
        expr_dict = expr if isinstance(expr, dict) else {"kind": "unknown"}
        kind = expr_dict.get("kind", "unknown")

        result: InferenceResult

        if kind == "literal":
            result = self._infer_literal(expr_dict)
        elif kind == "identifier":
            result = self._infer_identifier(expr_dict, context)
        elif kind == "call":
            result = self._infer_call(expr_dict, context)
        elif kind == "property":
            result = self._infer_property(expr_dict, context)
        elif kind == "array":
            result = self._infer_array(expr_dict, context)
        elif kind == "object":
            result = self._infer_object(expr_dict, context)
        elif kind == "function":
            result = self._infer_function_expr(expr_dict, context)
        else:
            # Unknown expression kind - return unknown type
            result = InferenceResult(
                inferred_type=Type("unknown"),
                confidence=0.0
            )

        self.inference_cache[cache_key] = result
        return result

    def check_expression(
        self,
        expr: Any,
        expected: Type,
        context: TypeContext
    ) -> bool:
        """
        Check if an expression can have the expected type.

        Args:
            expr: Expression to check
            expected: Expected type
            context: Type context

        Returns:
            True if expression can have expected type

        Example:
            >>> engine = TypeInferenceEngine()
            >>> context = TypeContext()
            >>> expr = {"kind": "literal", "value": 42}
            >>> engine.check_expression(expr, Type("number"), context)
            True
        """
        result = self.infer_expression(expr, context)
        return self._is_assignable(result.inferred_type, expected)

    def infer_forward(
        self,
        node: Any,
        context: TypeContext
    ) -> Type:
        """
        Forward pass: infer type from context (bottom-up).

        Synthesizes type information from leaves to root.

        Args:
            node: AST node to infer type for
            context: Current type context

        Returns:
            Inferred type
        """
        result = self.infer_expression(node, context)
        return result.inferred_type

    def infer_backward(
        self,
        node: Any,
        usage_type: Type,
        context: TypeContext
    ) -> Type:
        """
        Backward pass: refine type from usage (top-down).

        Propagates type information from root to leaves based on
        how the value is used.

        Args:
            node: AST node to refine type for
            usage_type: Type expected from usage
            context: Current type context

        Returns:
            Refined type

        Example:
            >>> engine = TypeInferenceEngine()
            >>> # If we know the result is used as a string, refine the type
            >>> node = {"kind": "identifier", "name": "x"}
            >>> context = TypeContext(variables={"x": Type("string", nullable=True)})
            >>> refined = engine.infer_backward(node, Type("string"), context)
            >>> print(refined.nullable)
            False
        """
        forward_type = self.infer_forward(node, context)

        # Try to narrow the type based on usage
        if forward_type.nullable and not usage_type.nullable:
            # Remove nullability if usage requires non-null
            non_null_forward = Type(
                forward_type.name,
                forward_type.parameters,
                nullable=False,
                metadata=forward_type.metadata
            )
            # Check if non-null version matches usage
            if non_null_forward == usage_type:
                return non_null_forward

        # If forward type is compatible with usage, use forward type
        if self._is_assignable(forward_type, usage_type):
            return forward_type

        # Otherwise, prefer usage type
        return usage_type

    def unify(
        self,
        type1: Type,
        type2: Type
    ) -> Optional[Dict[str, Type]]:
        """
        Unify two types, returning substitution if possible.

        Attempts to find a substitution for type variables that makes
        the two types equivalent.

        Args:
            type1: First type
            type2: Second type

        Returns:
            Dictionary of variable substitutions, or None if unification fails

        Example:
            >>> engine = TypeInferenceEngine()
            >>> # Unify Array<T> with Array<number>
            >>> generic = Type("Array", (Type("T"),))
            >>> concrete = Type("Array", (Type("number"),))
            >>> subst = engine.unify(generic, concrete)
            >>> print(subst)
            {'T': Type(name='number')}
        """
        subst: Dict[str, Type] = {}

        if not self._unify_helper(type1, type2, subst):
            return None

        return subst

    def apply_substitution(
        self,
        type: Type,
        subst: Dict[str, Type]
    ) -> Type:
        """
        Apply type variable substitution to a type.

        Args:
            type: Type to apply substitution to
            subst: Substitution dictionary

        Returns:
            Type with substitutions applied
        """
        return type.substitute(subst)

    # Private helper methods

    def _cache_key(self, expr: Any, context: TypeContext) -> int:
        """Generate cache key for expression and context."""
        # Simple hash based on expression and context variables
        expr_str = str(expr)
        context_str = str(sorted(context.variables.items()))
        return hash(expr_str + context_str)

    def _infer_literal(self, expr: Dict[str, Any]) -> InferenceResult:
        """Infer type of literal value."""
        value = expr.get("value")

        if isinstance(value, bool):
            return InferenceResult(inferred_type=Type("boolean"))
        elif isinstance(value, int) or isinstance(value, float):
            return InferenceResult(inferred_type=Type("number"))
        elif isinstance(value, str):
            return InferenceResult(inferred_type=Type("string"))
        elif value is None:
            return InferenceResult(inferred_type=Type("null"))
        else:
            return InferenceResult(
                inferred_type=Type("unknown"),
                confidence=0.0
            )

    def _infer_identifier(
        self,
        expr: Dict[str, Any],
        context: TypeContext
    ) -> InferenceResult:
        """Infer type of identifier from context."""
        name = expr.get("name", "")

        # Look up in context
        type_found = context.lookup(name)

        if type_found:
            return InferenceResult(inferred_type=type_found)
        else:
            # Unknown identifier
            return InferenceResult(
                inferred_type=Type("unknown"),
                confidence=0.0
            )

    def _infer_call(
        self,
        expr: Dict[str, Any],
        context: TypeContext
    ) -> InferenceResult:
        """Infer type of function call."""
        callee = expr.get("callee", {})
        args = expr.get("arguments", [])

        # Infer callee type
        callee_result = self.infer_expression(callee, context)
        callee_type = callee_result.inferred_type

        # If callee is a function type, return its return type
        if callee_type.is_function() and callee_type.parameters:
            # Last parameter is return type
            return_type = callee_type.parameters[-1]
            return InferenceResult(inferred_type=return_type)

        # Unknown function
        return InferenceResult(
            inferred_type=Type("unknown"),
            confidence=0.0
        )

    def _infer_property(
        self,
        expr: Dict[str, Any],
        context: TypeContext
    ) -> InferenceResult:
        """Infer type of property access."""
        object_expr = expr.get("object", {})
        property_name = expr.get("property", "")

        # Infer object type
        object_result = self.infer_expression(object_expr, context)
        object_type = object_result.inferred_type

        # Look up property type in classes/interfaces
        if object_type.name in context.classes:
            class_type = context.classes[object_type.name]
            if property_name in class_type.properties:
                return InferenceResult(
                    inferred_type=class_type.properties[property_name]
                )

        if object_type.name in context.interfaces:
            interface_type = context.interfaces[object_type.name]
            if property_name in interface_type.properties:
                return InferenceResult(
                    inferred_type=interface_type.properties[property_name]
                )

        # Unknown property
        return InferenceResult(
            inferred_type=Type("unknown"),
            confidence=0.0
        )

    def _infer_array(
        self,
        expr: Dict[str, Any],
        context: TypeContext
    ) -> InferenceResult:
        """Infer type of array literal."""
        elements = expr.get("elements", [])

        if not elements:
            # Empty array - Array<unknown>
            return InferenceResult(
                inferred_type=Type("Array", (Type("unknown"),)),
                confidence=0.5
            )

        # Infer types of all elements
        element_types = [
            self.infer_expression(elem, context).inferred_type
            for elem in elements
        ]

        # Find common type (simplified - just use first element type)
        # In full implementation, would compute least upper bound
        common_type = element_types[0]

        return InferenceResult(
            inferred_type=Type("Array", (common_type,))
        )

    def _infer_object(
        self,
        expr: Dict[str, Any],
        context: TypeContext
    ) -> InferenceResult:
        """Infer type of object literal."""
        properties = expr.get("properties", [])

        # Infer types of all properties
        # For now, return generic object type
        # Full implementation would create anonymous object type
        return InferenceResult(
            inferred_type=Type("object"),
            confidence=0.8
        )

    def _infer_function_expr(
        self,
        expr: Dict[str, Any],
        context: TypeContext
    ) -> InferenceResult:
        """Infer type of function expression."""
        params = expr.get("parameters", [])
        return_type = expr.get("returnType")

        # Extract parameter types
        param_types = []
        for param in params:
            if isinstance(param, dict) and "type" in param:
                param_types.append(Type(param["type"]))
            else:
                param_types.append(Type("unknown"))

        # Extract return type
        if return_type:
            ret = Type(return_type) if isinstance(return_type, str) else Type("unknown")
        else:
            ret = Type("unknown")

        # Create function type
        function_type = Type("function", tuple(param_types + [ret]))

        return InferenceResult(inferred_type=function_type)

    def _is_assignable(self, source: Type, target: Type) -> bool:
        """
        Check if source type is assignable to target type.

        Implements simplified subtyping rules:
        - Exact match
        - Nullable to non-nullable (unsafe, but allowed)
        - Unknown is assignable to anything
        """
        # Exact match
        if source == target:
            return True

        # Unknown is assignable to anything
        if source.name == "unknown" or target.name == "unknown":
            return True

        # Nullable source can be assigned to non-nullable target
        # (unsafe, but common in gradual typing)
        if source.nullable and not target.nullable:
            non_null_source = Type(
                source.name,
                source.parameters,
                nullable=False,
                metadata=source.metadata
            )
            return non_null_source == target

        # Generic types must match structure
        if source.parameters and target.parameters:
            if source.name == target.name and len(source.parameters) == len(target.parameters):
                return all(
                    self._is_assignable(s, t)
                    for s, t in zip(source.parameters, target.parameters)
                )

        return False

    def _unify_helper(
        self,
        type1: Type,
        type2: Type,
        subst: Dict[str, Type]
    ) -> bool:
        """
        Helper for unification with accumulating substitution.

        Returns True if unification succeeds, False otherwise.
        Modifies subst in place.
        """
        # Apply existing substitution
        type1 = type1.substitute(subst)
        type2 = type2.substitute(subst)

        # Same type - success
        if type1 == type2:
            return True

        # Type variable in type1
        if type1.name not in PRIMITIVE_TYPES and not type1.parameters:
            # Check if already has a substitution
            if type1.name in subst:
                # Must unify with existing substitution
                return self._unify_helper(subst[type1.name], type2, subst)
            else:
                # Add new substitution
                subst[type1.name] = type2
                return True

        # Type variable in type2
        if type2.name not in PRIMITIVE_TYPES and not type2.parameters:
            # Check if already has a substitution
            if type2.name in subst:
                # Must unify with existing substitution
                return self._unify_helper(type1, subst[type2.name], subst)
            else:
                # Add new substitution
                subst[type2.name] = type1
                return True

        # Generic types - must have same name and unify parameters
        if type1.parameters and type2.parameters:
            if type1.name == type2.name and len(type1.parameters) == len(type2.parameters):
                return all(
                    self._unify_helper(t1, t2, subst)
                    for t1, t2 in zip(type1.parameters, type2.parameters)
                )

        # Failed to unify
        return False


# Re-export for cleaner imports
__all__ = [
    "TypeConstraint",
    "InferenceResult",
    "TypeInferenceEngine",
]
