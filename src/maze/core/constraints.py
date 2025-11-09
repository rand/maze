"""
Constraint abstractions for the Maze code generation system.

This module defines the hierarchical constraint system that guides
code generation through syntactic, type, semantic, and contextual constraints.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from enum import Enum
import hashlib
import json

from maze.core.types import Type, TypeContext, ConstraintLevel, Diagnostic


@dataclass
class TokenMask:
    """
    Token mask representing allowed/forbidden tokens at a generation point.

    This is the core output from constraint evaluation that guides the LLM
    to generate only valid tokens.
    """
    allowed_tokens: Optional[Set[int]] = None  # None means all allowed
    forbidden_tokens: Optional[Set[int]] = None  # None means none forbidden
    logit_bias: Optional[Dict[int, float]] = None  # Token ID -> bias

    def is_allowed(self, token_id: int) -> bool:
        """Check if a token is allowed."""
        if self.forbidden_tokens and token_id in self.forbidden_tokens:
            return False
        if self.allowed_tokens is not None:
            return token_id in self.allowed_tokens
        return True

    def merge(self, other: TokenMask) -> TokenMask:
        """Merge with another mask (intersection of allowed sets)."""
        result = TokenMask()

        # Merge allowed tokens (intersection if both present)
        if self.allowed_tokens is not None and other.allowed_tokens is not None:
            result.allowed_tokens = self.allowed_tokens & other.allowed_tokens
        elif self.allowed_tokens is not None:
            result.allowed_tokens = self.allowed_tokens
        elif other.allowed_tokens is not None:
            result.allowed_tokens = other.allowed_tokens

        # Merge forbidden tokens (union if present)
        if self.forbidden_tokens or other.forbidden_tokens:
            result.forbidden_tokens = (self.forbidden_tokens or set()) | (other.forbidden_tokens or set())

        # Merge logit biases
        if self.logit_bias or other.logit_bias:
            result.logit_bias = {**(self.logit_bias or {}), **(other.logit_bias or {})}

        return result


@dataclass
class GenerationState:
    """
    Current state during generation for constraint evaluation.
    """
    generated_text: str
    context: TypeContext
    current_position: int
    tokens_generated: int
    language: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def copy(self) -> GenerationState:
        """Create a copy of the current state."""
        return GenerationState(
            generated_text=self.generated_text,
            context=self.context.copy(),
            current_position=self.current_position,
            tokens_generated=self.tokens_generated,
            language=self.language,
            metadata=self.metadata.copy()
        )


class Constraint(ABC):
    """
    Base class for all constraints in the system.

    Constraints evaluate the current generation state and produce
    token masks that guide the LLM towards valid completions.
    """

    def __init__(self, level: ConstraintLevel, weight: float = 1.0):
        """
        Initialize constraint.

        Args:
            level: The constraint level in the hierarchy
            weight: Weight for soft constraints (0.0 to 1.0)
        """
        self.level = level
        self.weight = weight
        self._cache_key: Optional[str] = None

    @abstractmethod
    def evaluate(self, state: GenerationState) -> TokenMask:
        """
        Evaluate the constraint at the current generation state.

        Args:
            state: Current generation state

        Returns:
            TokenMask indicating allowed/forbidden tokens
        """
        pass

    @abstractmethod
    def to_grammar(self) -> Optional[str]:
        """
        Convert constraint to grammar representation if possible.

        Returns:
            Grammar string (Lark format) or None if not representable
        """
        pass

    def cache_key(self) -> str:
        """Generate a cache key for this constraint."""
        if self._cache_key is None:
            content = f"{self.__class__.__name__}:{self.level}:{self.weight}"
            self._cache_key = hashlib.sha256(content.encode()).hexdigest()[:16]
        return self._cache_key

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(level={self.level.name}, weight={self.weight})"


@dataclass
class SyntacticConstraint(Constraint):
    """
    Syntactic constraints based on language grammar (CFG/Lark).

    These ensure the generated code follows valid syntax for the target language.
    """

    grammar: str  # Lark grammar specification
    start_rule: str = "start"
    language: str = "typescript"

    def __init__(self, grammar: str, start_rule: str = "start", language: str = "typescript"):
        super().__init__(ConstraintLevel.SYNTACTIC)
        self.grammar = grammar
        self.start_rule = start_rule
        self.language = language

    def evaluate(self, state: GenerationState) -> TokenMask:
        """Evaluate using CFG parser state."""
        # In production, this would interface with llguidance
        # to compute valid next tokens based on parser state
        return TokenMask()

    def to_grammar(self) -> str:
        """Return the Lark grammar."""
        return self.grammar

    @classmethod
    def from_language(cls, language: str) -> SyntacticConstraint:
        """Create syntactic constraint for a language."""
        # Simplified - would load from grammar files
        grammar_templates = {
            "typescript": """
                ?start: statement+
                statement: assignment | function_def | import_stmt
                assignment: IDENT "=" expression ";"
                function_def: "function" IDENT "(" params? ")" block
                import_stmt: "import" import_spec "from" STRING ";"
                IDENT: /[a-zA-Z_][a-zA-Z0-9_]*/
                STRING: /"[^"]*"/ | /'[^']*/
                %ignore /\\s+/
            """,
            "python": """
                ?start: statement+
                statement: assignment | function_def | import_stmt
                assignment: IDENT "=" expression
                function_def: "def" IDENT "(" params? ")" ":" block
                import_stmt: "import" module_name
                IDENT: /[a-zA-Z_][a-zA-Z0-9_]*/
                %ignore /\\s+/
            """
        }

        grammar = grammar_templates.get(language, grammar_templates["typescript"])
        return cls(grammar=grammar, language=language)


@dataclass
class TypeConstraint(Constraint):
    """
    Type-based constraints ensuring type correctness.

    These use type inhabitation and type checking to ensure
    generated code is type-safe.
    """

    expected_type: Type
    context: TypeContext
    strict: bool = True

    def __init__(self, expected_type: Type, context: TypeContext, strict: bool = True):
        super().__init__(ConstraintLevel.TYPE)
        self.expected_type = expected_type
        self.context = context
        self.strict = strict

    def evaluate(self, state: GenerationState) -> TokenMask:
        """Evaluate type constraints."""
        # In production, this would:
        # 1. Parse the partial AST
        # 2. Infer types of available expressions
        # 3. Find paths to expected_type using inhabitation search
        # 4. Mask tokens that can't lead to valid type
        return TokenMask()

    def to_grammar(self) -> Optional[str]:
        """Generate type-specific grammar rules."""
        # Could generate grammar rules that encode type constraints
        # For example, if expecting string, only allow string literals,
        # string variables, and string-returning functions
        return None

    def find_valid_expressions(self) -> List[str]:
        """
        Find expressions in context that match the expected type.

        Returns:
            List of valid expressions that have the expected type
        """
        valid = []

        # Check variables
        for var_name, var_type in self.context.variables.items():
            if self.types_compatible(var_type, self.expected_type):
                valid.append(var_name)

        # Check functions (if return type matches)
        for func_name, func_sig in self.context.functions.items():
            if self.types_compatible(func_sig.return_type, self.expected_type):
                # Would need to check if we can satisfy parameter types
                valid.append(f"{func_name}(...)")

        return valid

    def types_compatible(self, actual: Type, expected: Type) -> bool:
        """Check if actual type is compatible with expected type."""
        if not self.strict:
            # Loose compatibility - just check base types
            return actual.name == expected.name

        # Strict compatibility
        if actual == expected:
            return True

        # Check nullable compatibility
        if expected.nullable and not actual.nullable:
            return self.types_compatible(actual, Type(expected.name, expected.parameters, False))

        # Check generic compatibility
        if actual.name == expected.name and len(actual.parameters) == len(expected.parameters):
            return all(
                self.types_compatible(a, e)
                for a, e in zip(actual.parameters, expected.parameters)
            )

        return False


@dataclass
class SemanticConstraint(Constraint):
    """
    Semantic constraints based on behavioral specifications.

    These ensure the generated code satisfies functional requirements,
    passes tests, and meets specifications.
    """

    specification: str
    test_cases: List[Dict[str, Any]] = field(default_factory=list)
    properties: List[str] = field(default_factory=list)
    invariants: List[str] = field(default_factory=list)

    def __init__(self, specification: str):
        super().__init__(ConstraintLevel.SEMANTIC)
        self.specification = specification
        self.test_cases = []
        self.properties = []
        self.invariants = []

    def evaluate(self, state: GenerationState) -> TokenMask:
        """Evaluate semantic constraints."""
        # This is typically enforced in post-validation rather than
        # during generation, but could potentially guide generation
        # based on symbolic execution or property checking
        return TokenMask()

    def to_grammar(self) -> Optional[str]:
        """Semantic constraints typically can't be encoded as grammar."""
        return None

    def add_test_case(self, input: Any, expected_output: Any) -> None:
        """Add a test case."""
        self.test_cases.append({
            "input": input,
            "expected": expected_output
        })

    def add_property(self, property: str) -> None:
        """Add a property that must hold."""
        self.properties.append(property)

    def add_invariant(self, invariant: str) -> None:
        """Add an invariant that must be preserved."""
        self.invariants.append(invariant)


@dataclass
class ContextualConstraint(Constraint):
    """
    Contextual constraints based on learned patterns.

    These are soft constraints that guide generation towards
    project-specific conventions and patterns.
    """

    patterns: List[str] = field(default_factory=list)
    anti_patterns: List[str] = field(default_factory=list)
    style_rules: Dict[str, Any] = field(default_factory=dict)
    weight_map: Dict[str, float] = field(default_factory=dict)

    def __init__(self, weight: float = 0.5):
        super().__init__(ConstraintLevel.CONTEXTUAL, weight)
        self.patterns = []
        self.anti_patterns = []
        self.style_rules = {}
        self.weight_map = {}

    def evaluate(self, state: GenerationState) -> TokenMask:
        """Evaluate contextual constraints."""
        # Apply soft biases based on patterns
        mask = TokenMask()
        mask.logit_bias = {}

        # This would analyze patterns and apply appropriate biases
        # to tokens that match or violate patterns

        return mask

    def to_grammar(self) -> Optional[str]:
        """Contextual constraints are typically not strict grammar."""
        return None

    def add_pattern(self, pattern: str, weight: float = 1.0) -> None:
        """Add a positive pattern to encourage."""
        self.patterns.append(pattern)
        self.weight_map[pattern] = weight

    def add_anti_pattern(self, pattern: str, weight: float = -1.0) -> None:
        """Add a negative pattern to discourage."""
        self.anti_patterns.append(pattern)
        self.weight_map[pattern] = weight


@dataclass
class JSONSchemaConstraint(Constraint):
    """
    Constraint based on JSON Schema for structured output.

    Useful for tool calls, configuration, and structured data generation.
    """

    schema: Dict[str, Any]

    def __init__(self, schema: Dict[str, Any]):
        super().__init__(ConstraintLevel.SYNTACTIC)
        self.schema = schema

    def evaluate(self, state: GenerationState) -> TokenMask:
        """Evaluate JSON schema constraints."""
        # Would validate partial JSON against schema
        # and mask invalid tokens
        return TokenMask()

    def to_grammar(self) -> str:
        """Convert JSON Schema to Lark grammar."""
        # Simplified version - production would handle full JSON Schema spec
        return f"""
            ?start: json_value
            json_value: object | array | string | number | boolean | null
            object: "{{" [pair ("," pair)*] "}}"
            pair: string ":" json_value
            array: "[" [json_value ("," json_value)*] "]"
            string: ESCAPED_STRING
            number: SIGNED_NUMBER
            boolean: "true" | "false"
            null: "null"

            ESCAPED_STRING: /"[^"]*"/
            SIGNED_NUMBER: /-?\\d+(\\.\\d+)?([eE][+-]?\\d+)?/

            %ignore /\\s+/
        """

    def to_json_schema_string(self) -> str:
        """Get JSON representation of the schema."""
        return json.dumps(self.schema, indent=2)


@dataclass
class RegexConstraint(Constraint):
    """
    Constraint based on regular expressions.

    Useful for enforcing naming conventions, format requirements, etc.
    """

    pattern: str
    applies_to: str = "identifiers"  # What this regex applies to

    def __init__(self, pattern: str, applies_to: str = "identifiers"):
        super().__init__(ConstraintLevel.SYNTACTIC)
        self.pattern = pattern
        self.applies_to = applies_to

    def evaluate(self, state: GenerationState) -> TokenMask:
        """Evaluate regex constraints."""
        # Would check if current position expects an identifier/string
        # that must match the regex, and mask accordingly
        return TokenMask()

    def to_grammar(self) -> str:
        """Convert regex to grammar rule."""
        return f'PATTERN: /{self.pattern}/'


@dataclass
class ConstraintSet:
    """
    Collection of constraints organized by level.

    This represents the complete set of constraints that will
    guide a generation task.
    """

    syntactic: List[SyntacticConstraint] = field(default_factory=list)
    type_based: List[TypeConstraint] = field(default_factory=list)
    semantic: List[SemanticConstraint] = field(default_factory=list)
    contextual: List[ContextualConstraint] = field(default_factory=list)

    # Additional constraint types
    json_schemas: List[JSONSchemaConstraint] = field(default_factory=list)
    regex_patterns: List[RegexConstraint] = field(default_factory=list)

    def add(self, constraint: Constraint) -> None:
        """Add a constraint to the appropriate level."""
        if isinstance(constraint, SyntacticConstraint):
            self.syntactic.append(constraint)
        elif isinstance(constraint, TypeConstraint):
            self.type_based.append(constraint)
        elif isinstance(constraint, SemanticConstraint):
            self.semantic.append(constraint)
        elif isinstance(constraint, ContextualConstraint):
            self.contextual.append(constraint)
        elif isinstance(constraint, JSONSchemaConstraint):
            self.json_schemas.append(constraint)
        elif isinstance(constraint, RegexConstraint):
            self.regex_patterns.append(constraint)
        else:
            raise ValueError(f"Unknown constraint type: {type(constraint)}")

    def evaluate(self, state: GenerationState) -> TokenMask:
        """
        Evaluate all constraints and merge masks.

        Constraints are evaluated in order of their level (syntactic first,
        then type, semantic, and finally contextual).
        """
        mask = TokenMask()

        # Evaluate in hierarchical order
        for constraint_list in [
            self.syntactic,
            self.json_schemas,
            self.regex_patterns,
            self.type_based,
            self.semantic,
            self.contextual
        ]:
            for constraint in constraint_list:
                constraint_mask = constraint.evaluate(state)
                mask = mask.merge(constraint_mask)

        return mask

    def to_grammar(self) -> Optional[str]:
        """
        Combine constraints into a unified grammar if possible.

        Returns the most specific grammar that can represent
        the constraints, prioritizing syntactic constraints.
        """
        # Prioritize explicit syntactic constraints
        if self.syntactic:
            return self.syntactic[0].to_grammar()

        # Fall back to JSON schema if present
        if self.json_schemas:
            return self.json_schemas[0].to_grammar()

        # Otherwise, try to generate from other constraints
        for constraint in self.type_based + self.semantic + self.contextual:
            if grammar := constraint.to_grammar():
                return grammar

        return None

    def to_pattern(self) -> str:
        """Generate a pattern string for learning/caching."""
        components = []

        if self.syntactic:
            components.append(f"syn:{len(self.syntactic)}")
        if self.type_based:
            components.append(f"type:{len(self.type_based)}")
        if self.semantic:
            components.append(f"sem:{len(self.semantic)}")
        if self.contextual:
            components.append(f"ctx:{len(self.contextual)}")
        if self.json_schemas:
            components.append(f"json:{len(self.json_schemas)}")
        if self.regex_patterns:
            components.append(f"regex:{len(self.regex_patterns)}")

        return ",".join(components) if components else "empty"

    def get_all(self) -> List[Constraint]:
        """
        Get all constraints as a flat list.

        Returns:
            List of all constraints in the set
        """
        all_constraints = []
        all_constraints.extend(self.syntactic)
        all_constraints.extend(self.type_based)
        all_constraints.extend(self.semantic)
        all_constraints.extend(self.contextual)
        all_constraints.extend(self.json_schemas)
        all_constraints.extend(self.regex_patterns)
        return all_constraints

    @classmethod
    def from_list(cls, constraints: List[Constraint]) -> "ConstraintSet":
        """
        Create a ConstraintSet from a list of constraints.

        Args:
            constraints: List of constraints to add

        Returns:
            New ConstraintSet with all constraints added
        """
        constraint_set = cls()
        for constraint in constraints:
            constraint_set.add(constraint)
        return constraint_set

    def cache_key(self) -> str:
        """Generate cache key for this constraint set."""
        content = self.to_pattern()
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def copy(self) -> ConstraintSet:
        """Create a deep copy of the constraint set."""
        return ConstraintSet(
            syntactic=self.syntactic.copy(),
            type_based=self.type_based.copy(),
            semantic=self.semantic.copy(),
            contextual=self.contextual.copy(),
            json_schemas=self.json_schemas.copy(),
            regex_patterns=self.regex_patterns.copy()
        )

    def diff(self, other: ConstraintSet) -> List[str]:
        """
        Get differences between this and another constraint set.

        Returns:
            List of difference descriptions
        """
        differences = []

        if len(self.syntactic) != len(other.syntactic):
            differences.append(f"Syntactic: {len(self.syntactic)} -> {len(other.syntactic)}")

        if len(self.type_based) != len(other.type_based):
            differences.append(f"Type: {len(self.type_based)} -> {len(other.type_based)}")

        if len(self.semantic) != len(other.semantic):
            differences.append(f"Semantic: {len(self.semantic)} -> {len(other.semantic)}")

        if len(self.contextual) != len(other.contextual):
            differences.append(f"Contextual: {len(self.contextual)} -> {len(other.contextual)}")

        return differences

    def __str__(self) -> str:
        return f"ConstraintSet({self.to_pattern()})"


# Re-export commonly used types
__all__ = [
    "Constraint",
    "ConstraintLevel",
    "ConstraintSet",
    "SyntacticConstraint",
    "TypeConstraint",
    "SemanticConstraint",
    "ContextualConstraint",
    "JSONSchemaConstraint",
    "RegexConstraint",
    "TokenMask",
    "GenerationState",
]