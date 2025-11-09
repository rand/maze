"""
Core type system for the Maze constraint-based code generation system.

This module provides the foundational type representations used throughout
the system for type-directed synthesis and constraint generation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import (
    Any, Dict, List, Optional, Tuple, Union, Set,
    Literal, Protocol, runtime_checkable
)
from enum import Enum
from datetime import datetime
import hashlib


@dataclass(frozen=True)
class Type:
    """
    Universal type representation across all supported languages.

    Examples:
        - Type("string") - primitive string type
        - Type("Array", [Type("number")]) - array of numbers
        - Type("Promise", [Type("User")]) - Promise<User>
        - Type("function", [Type("number"), Type("string")]) - number => string
    """
    name: str
    parameters: Tuple[Type, ...] = field(default_factory=tuple)
    nullable: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __hash__(self) -> int:
        """Generate hash for type caching."""
        return hash((self.name, self.parameters, self.nullable))

    def __str__(self) -> str:
        """Human-readable string representation."""
        if self.parameters:
            params = ", ".join(str(p) for p in self.parameters)
            base = f"{self.name}<{params}>"
        else:
            base = self.name

        if self.nullable:
            return f"{base}?"
        return base

    def is_primitive(self) -> bool:
        """Check if this is a primitive type."""
        return self.name in PRIMITIVE_TYPES and not self.parameters

    def is_function(self) -> bool:
        """Check if this is a function type."""
        return self.name == "function"

    def is_generic(self) -> bool:
        """Check if this type has generic parameters."""
        return bool(self.parameters)

    def substitute(self, mapping: Dict[str, Type]) -> Type:
        """Substitute type variables with concrete types."""
        if self.name in mapping:
            return mapping[self.name]

        if self.parameters:
            new_params = tuple(p.substitute(mapping) for p in self.parameters)
            return Type(self.name, new_params, self.nullable, self.metadata)

        return self


# Common primitive types across languages
PRIMITIVE_TYPES = {
    "string", "number", "boolean", "null", "undefined", "void",
    "int", "float", "double", "char", "byte",
    "str", "bool", "int", "float", "None",  # Python
    "i8", "i16", "i32", "i64", "u8", "u16", "u32", "u64", "f32", "f64", "usize", "isize",  # Rust
    "rune",  # Go
    "u8", "u16", "u32", "u64", "i8", "i16", "i32", "i64", "f16", "f32", "f64", "f128",  # Zig
}


@dataclass
class TypeVariable:
    """Type variable for generic/polymorphic types."""
    name: str
    constraints: List[Type] = field(default_factory=list)

    def __str__(self) -> str:
        if self.constraints:
            constraints = " extends " + " & ".join(str(c) for c in self.constraints)
            return f"{self.name}{constraints}"
        return self.name


@dataclass
class TypeParameter:
    """Parameter in a type signature."""
    name: str
    type: Type
    optional: bool = False
    default_value: Optional[Any] = None

    def __str__(self) -> str:
        opt = "?" if self.optional else ""
        base = f"{self.name}{opt}: {self.type}"
        if self.default_value is not None:
            return f"{base} = {self.default_value}"
        return base


@dataclass
class FunctionSignature:
    """Complete function signature with parameters and return type."""
    name: str
    parameters: List[TypeParameter]
    return_type: Type
    type_parameters: List[TypeVariable] = field(default_factory=list)
    throws: List[Type] = field(default_factory=list)
    is_async: bool = False
    is_generator: bool = False

    def to_type(self) -> Type:
        """Convert to function Type representation."""
        param_types = [p.type for p in self.parameters]
        return Type("function", tuple(param_types + [self.return_type]))

    def __str__(self) -> str:
        type_params = ""
        if self.type_parameters:
            type_params = f"<{', '.join(str(tp) for tp in self.type_parameters)}>"

        params = ", ".join(str(p) for p in self.parameters)

        modifiers = []
        if self.is_async:
            modifiers.append("async")
        if self.is_generator:
            modifiers.append("generator")

        prefix = " ".join(modifiers) + " " if modifiers else ""

        base = f"{prefix}function {self.name}{type_params}({params}): {self.return_type}"

        if self.throws:
            throws = " | ".join(str(t) for t in self.throws)
            base += f" throws {throws}"

        return base


@dataclass
class TypeContext:
    """
    Type environment tracking available types, variables, and functions.

    This represents the typing context at a particular point in the code,
    including all accessible symbols and their types.
    """
    variables: Dict[str, Type] = field(default_factory=dict)
    functions: Dict[str, FunctionSignature] = field(default_factory=dict)
    classes: Dict[str, 'ClassType'] = field(default_factory=dict)
    interfaces: Dict[str, 'InterfaceType'] = field(default_factory=dict)
    type_aliases: Dict[str, Type] = field(default_factory=dict)
    imports: Dict[str, str] = field(default_factory=dict)

    # Language-specific context
    language: str = "typescript"
    strict_nulls: bool = True
    strict_types: bool = True

    def copy(self) -> TypeContext:
        """Create a deep copy of the context."""
        return TypeContext(
            variables=self.variables.copy(),
            functions=self.functions.copy(),
            classes=self.classes.copy(),
            interfaces=self.interfaces.copy(),
            type_aliases=self.type_aliases.copy(),
            imports=self.imports.copy(),
            language=self.language,
            strict_nulls=self.strict_nulls,
            strict_types=self.strict_types,
        )

    def merge(self, other: TypeContext) -> TypeContext:
        """Merge another context into a new context."""
        result = self.copy()
        result.variables.update(other.variables)
        result.functions.update(other.functions)
        result.classes.update(other.classes)
        result.interfaces.update(other.interfaces)
        result.type_aliases.update(other.type_aliases)
        result.imports.update(other.imports)
        return result

    def lookup(self, name: str) -> Optional[Type]:
        """Look up a symbol's type in the context."""
        if name in self.variables:
            return self.variables[name]
        if name in self.functions:
            return self.functions[name].to_type()
        if name in self.classes:
            return Type(name)
        if name in self.interfaces:
            return Type(name)
        if name in self.type_aliases:
            return self.type_aliases[name]
        return None


@dataclass
class ClassType:
    """Class/struct type representation."""
    name: str
    properties: Dict[str, Type]
    methods: Dict[str, FunctionSignature]
    extends: Optional[str] = None
    implements: List[str] = field(default_factory=list)
    type_parameters: List[TypeVariable] = field(default_factory=list)
    is_abstract: bool = False

    def to_type(self) -> Type:
        """Convert to Type representation."""
        if self.type_parameters:
            params = tuple(Type(tp.name) for tp in self.type_parameters)
            return Type(self.name, params)
        return Type(self.name)


@dataclass
class InterfaceType:
    """Interface/trait type representation."""
    name: str
    properties: Dict[str, Type]
    methods: Dict[str, FunctionSignature]
    extends: List[str] = field(default_factory=list)
    type_parameters: List[TypeVariable] = field(default_factory=list)

    def to_type(self) -> Type:
        """Convert to Type representation."""
        if self.type_parameters:
            params = tuple(Type(tp.name) for tp in self.type_parameters)
            return Type(self.name, params)
        return Type(self.name)


class ConstraintLevel(Enum):
    """
    Four-tier constraint hierarchy for progressive refinement.

    Each level provides different guarantees:
    - SYNTACTIC: Valid syntax according to language grammar
    - TYPE: Type-correct according to type system
    - SEMANTIC: Satisfies behavioral specifications
    - CONTEXTUAL: Follows project-specific patterns
    """
    SYNTACTIC = 1
    TYPE = 2
    SEMANTIC = 3
    CONTEXTUAL = 4


@dataclass
class IndexedContext:
    """
    Output from Stage 1: Context Indexer.

    Contains all extracted information from the codebase needed
    for constraint synthesis and code generation.
    """
    files: List[Dict[str, str]]
    symbols: List[Dict[str, Any]]
    schemas: List[Dict[str, Any]]
    style: Dict[str, Any]
    tests: List[Dict[str, str]]
    constraints_candidates: List[Dict[str, Any]]

    # Metadata
    language: str = "typescript"
    project_path: Optional[str] = None
    indexed_at: datetime = field(default_factory=datetime.now)

    def to_summary(self) -> str:
        """Generate summary for memory storage."""
        return (
            f"Context for {self.language} project with "
            f"{len(self.symbols)} symbols, {len(self.schemas)} schemas, "
            f"{len(self.files)} files"
        )

    def get_type_context(self) -> TypeContext:
        """Extract TypeContext from indexed symbols."""
        context = TypeContext(language=self.language)

        for symbol in self.symbols:
            if symbol.get("kind") == "variable":
                context.variables[symbol["name"]] = Type(symbol.get("type", "any"))
            elif symbol.get("kind") == "function":
                # Simplified - would parse full signature in production
                context.functions[symbol["name"]] = FunctionSignature(
                    name=symbol["name"],
                    parameters=[],
                    return_type=Type(symbol.get("return_type", "any"))
                )

        return context


@dataclass
class Diagnostic:
    """
    Diagnostic information from validation or compilation.

    Used to capture errors, warnings, and suggestions from various
    validation stages.
    """
    severity: Literal["error", "warning", "info", "hint"]
    category: Literal["syntax", "type", "semantic", "style", "performance"]
    message: str
    file: Optional[str] = None
    line: Optional[int] = None
    column: Optional[int] = None
    end_line: Optional[int] = None
    end_column: Optional[int] = None
    code: Optional[str] = None  # Error code (e.g., "TS2322")
    suggestion: Optional[str] = None
    related: List['Diagnostic'] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "severity": self.severity,
            "category": self.category,
            "message": self.message,
            "file": self.file,
            "line": self.line,
            "column": self.column,
            "code": self.code,
            "suggestion": self.suggestion,
        }

    def __str__(self) -> str:
        location = ""
        if self.file:
            location = f"{self.file}:"
            if self.line:
                location += f"{self.line}:"
                if self.column:
                    location += f"{self.column}:"

        code_str = f"[{self.code}] " if self.code else ""

        return f"{location} {self.severity}: {code_str}{self.message}"


@dataclass
class GenerationResult:
    """
    Result from code generation including metadata and metrics.
    """
    code: str
    success: bool
    language: str

    # Generation metadata
    provider: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    generation_time_ms: float

    # Constraint information
    constraints_used: Optional['ConstraintSet'] = None
    grammar_used: Optional[str] = None
    schema_used: Optional[Dict[str, Any]] = None

    # Performance metrics
    mask_computation_us: Optional[float] = None
    type_search_ms: Optional[float] = None

    # Provenance
    prompt: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 500
    attempts: int = 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "code": self.code,
            "success": self.success,
            "language": self.language,
            "provider": self.provider,
            "model": self.model,
            "tokens": {
                "prompt": self.prompt_tokens,
                "completion": self.completion_tokens,
                "total": self.total_tokens,
            },
            "generation_time_ms": self.generation_time_ms,
            "attempts": self.attempts,
        }


@dataclass
class ValidationResult:
    """
    Result from code validation with diagnostics and suggestions.
    """
    passed: bool
    diagnostics: List[Diagnostic] = field(default_factory=list)

    # Categorized results
    syntax_errors: List[Diagnostic] = field(default_factory=list)
    type_errors: List[Diagnostic] = field(default_factory=list)
    semantic_errors: List[Diagnostic] = field(default_factory=list)
    style_warnings: List[Diagnostic] = field(default_factory=list)

    # Test results
    tests_run: int = 0
    tests_passed: int = 0
    tests_failed: int = 0
    test_coverage: Optional[float] = None

    # Resource usage
    validation_time_ms: float = 0.0
    memory_used_mb: Optional[float] = None

    # Suggestions for repair
    suggestions: List[str] = field(default_factory=list)

    def get_errors(self) -> List[Diagnostic]:
        """Get all error-level diagnostics."""
        return [d for d in self.diagnostics if d.severity == "error"]

    def get_warnings(self) -> List[Diagnostic]:
        """Get all warning-level diagnostics."""
        return [d for d in self.diagnostics if d.severity == "warning"]

    @classmethod
    def combine(cls, results: List['ValidationResult']) -> 'ValidationResult':
        """Combine multiple validation results."""
        combined = ValidationResult(passed=all(r.passed for r in results))

        for result in results:
            combined.diagnostics.extend(result.diagnostics)
            combined.syntax_errors.extend(result.syntax_errors)
            combined.type_errors.extend(result.type_errors)
            combined.semantic_errors.extend(result.semantic_errors)
            combined.style_warnings.extend(result.style_warnings)
            combined.tests_run += result.tests_run
            combined.tests_passed += result.tests_passed
            combined.tests_failed += result.tests_failed
            combined.validation_time_ms += result.validation_time_ms
            combined.suggestions.extend(result.suggestions)

        return combined


@dataclass
class GenerationProvenance:
    """
    Complete history of a generation attempt for debugging and learning.
    """
    id: str = field(default_factory=lambda: hashlib.sha256().hexdigest()[:8])
    timestamp: datetime = field(default_factory=datetime.now)

    # Input
    prompt: str = ""
    specification: Optional['Specification'] = None
    context: Optional[IndexedContext] = None

    # Process
    constraints_synthesized: Optional['ConstraintSet'] = None
    generation_attempts: List[GenerationResult] = field(default_factory=list)
    validation_results: List[ValidationResult] = field(default_factory=list)
    repair_attempts: List['RepairResult'] = field(default_factory=list)

    # Output
    final_code: Optional[str] = None
    final_result: Optional[ValidationResult] = None

    # Metrics
    total_time_ms: float = 0.0
    total_tokens: int = 0
    total_attempts: int = 0

    def add_generation(self, result: GenerationResult) -> None:
        """Add a generation attempt to the provenance."""
        self.generation_attempts.append(result)
        self.total_tokens += result.total_tokens
        self.total_attempts += 1

    def add_validation(self, result: ValidationResult) -> None:
        """Add a validation result to the provenance."""
        self.validation_results.append(result)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "prompt": self.prompt,
            "final_code": self.final_code,
            "total_time_ms": self.total_time_ms,
            "total_tokens": self.total_tokens,
            "total_attempts": self.total_attempts,
            "success": self.final_result.passed if self.final_result else False,
        }


# Re-export commonly used types for cleaner imports
__all__ = [
    "Type",
    "TypeVariable",
    "TypeParameter",
    "FunctionSignature",
    "TypeContext",
    "ClassType",
    "InterfaceType",
    "ConstraintLevel",
    "IndexedContext",
    "Diagnostic",
    "GenerationResult",
    "ValidationResult",
    "GenerationProvenance",
    "PRIMITIVE_TYPES",
]