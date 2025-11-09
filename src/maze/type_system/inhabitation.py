"""
Type inhabitation solver for the Maze type system.

Implements depth-limited search to find transformation paths from source
to target types, enabling type-directed code synthesis.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple, Callable
from enum import Enum

from maze.core.types import (
    Type, TypeContext, FunctionSignature, ClassType, InterfaceType
)


@dataclass
class Operation:
    """
    Type transformation operation.

    Represents a way to transform one type into another, such as:
    - Variable lookup (Type(unknown) -> Type(T) from context)
    - Function application (Type(A) -> Type(B) via f: A -> B)
    - Property access (Type(Obj) -> Type(T) via obj.prop)
    - Type coercion (Type(A) -> Type(B) with conversion)

    Example:
        >>> # Function application: number -> string via String()
        >>> op = Operation(
        ...     name="call String()",
        ...     input_type=Type("number"),
        ...     output_type=Type("string"),
        ...     cost=1.0
        ... )
    """
    name: str
    input_type: Type
    output_type: Type
    cost: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def applicable(self, type: Type) -> bool:
        """
        Check if operation can apply to given type.

        Args:
            type: Type to check

        Returns:
            True if operation can transform this type
        """
        # Exact match or compatible generic
        if type == self.input_type:
            return True

        # Check if types are compatible (simplified)
        if type.name == self.input_type.name:
            # Same base type is compatible
            return True

        return False

    def apply(self, type: Type) -> Type:
        """
        Apply operation to type.

        Args:
            type: Input type

        Returns:
            Output type after transformation
        """
        return self.output_type

    def __str__(self) -> str:
        return f"{self.name}: {self.input_type} -> {self.output_type} (cost: {self.cost})"


@dataclass
class InhabitationPath:
    """
    Sequence of operations to reach target type.

    Represents a concrete plan for transforming a source type into a
    target type through a series of operations.

    Example:
        >>> # Path: number -> string via toString()
        >>> path = InhabitationPath(
        ...     operations=[Operation("toString", Type("number"), Type("string"))],
        ...     source=Type("number"),
        ...     target=Type("string")
        ... )
        >>> print(path.cost)
        1.0
    """
    operations: List[Operation]
    source: Type
    target: Type

    @property
    def cost(self) -> float:
        """
        Total cost of path.

        Returns:
            Sum of all operation costs
        """
        return sum(op.cost for op in self.operations)

    def to_code(self, source_expr: str) -> str:
        """
        Convert path to code expression.

        Args:
            source_expr: Source expression as string

        Returns:
            Code that applies all operations

        Example:
            >>> path = InhabitationPath([
            ...     Operation("toString", Type("number"), Type("string"))
            ... ], Type("number"), Type("string"))
            >>> code = path.to_code("x")
            >>> print(code)
            x.toString()
        """
        expr = source_expr
        for op in self.operations:
            # Simple transformation based on operation name
            if op.name.startswith("call "):
                func_name = op.name[5:]  # Remove "call " prefix
                expr = f"{func_name}({expr})"
            elif op.name.startswith("access "):
                prop_name = op.name[7:]  # Remove "access " prefix
                expr = f"{expr}.{prop_name}"
            elif op.name.startswith("use "):
                var_name = op.name[4:]  # Remove "use " prefix
                expr = var_name
            else:
                # Generic operation
                expr = f"{op.name}({expr})"

        return expr

    def __str__(self) -> str:
        ops_str = " -> ".join(op.name for op in self.operations)
        return f"{self.source} => {self.target} via [{ops_str}] (cost: {self.cost})"


class InhabitationSolver:
    """
    Solver for type inhabitation problems.

    Finds transformation paths from source types to target types using
    depth-limited search with memoization and pruning.

    Performance target: <1ms with caching, <5 iterations convergence
    """

    def __init__(self, max_depth: int = 5, cache_size: int = 1000):
        """
        Initialize inhabitation solver.

        Args:
            max_depth: Maximum search depth
            cache_size: Maximum cache entries (LRU eviction)
        """
        self.max_depth = max_depth
        self.cache_size = cache_size
        self.cache: Dict[Tuple[Type, Type, int], List[InhabitationPath]] = {}
        self.cache_hits = 0
        self.cache_misses = 0

    def find_paths(
        self,
        source: Type,
        target: Type,
        context: TypeContext,
        max_results: int = 10
    ) -> List[InhabitationPath]:
        """
        Find all inhabitation paths from source to target.

        Args:
            source: Source type
            target: Target type
            context: Type context with available operations
            max_results: Maximum number of paths to return

        Returns:
            List of inhabitation paths, sorted by cost

        Example:
            >>> solver = InhabitationSolver()
            >>> context = TypeContext(variables={"x": Type("number")})
            >>> paths = solver.find_paths(Type("unknown"), Type("number"), context)
            >>> print(len(paths))
            1
        """
        # Check cache
        context_hash = self._context_hash(context)
        cache_key = (source, target, context_hash)

        if cache_key in self.cache:
            self.cache_hits += 1
            return self.cache[cache_key][:max_results]

        self.cache_misses += 1

        # Perform search
        paths = self._search(source, target, context, depth=0, visited=set())

        # Sort by cost
        paths.sort(key=lambda p: p.cost)

        # Limit results
        paths = paths[:max_results]

        # Cache results (with LRU eviction if needed)
        if len(self.cache) >= self.cache_size:
            # Simple LRU: remove first item
            self.cache.pop(next(iter(self.cache)))

        self.cache[cache_key] = paths

        return paths

    def find_best_path(
        self,
        source: Type,
        target: Type,
        context: TypeContext
    ) -> Optional[InhabitationPath]:
        """
        Find lowest-cost inhabitation path.

        Args:
            source: Source type
            target: Target type
            context: Type context

        Returns:
            Best path, or None if no path exists

        Example:
            >>> solver = InhabitationSolver()
            >>> context = TypeContext(variables={"x": Type("number")})
            >>> path = solver.find_best_path(Type("unknown"), Type("number"), context)
            >>> print(path.cost)
            0.0
        """
        paths = self.find_paths(source, target, context, max_results=1)
        return paths[0] if paths else None

    def is_inhabitable(
        self,
        target: Type,
        context: TypeContext
    ) -> bool:
        """
        Check if target type can be inhabited from context.

        Args:
            target: Target type to check
            context: Type context

        Returns:
            True if at least one inhabitation path exists

        Example:
            >>> solver = InhabitationSolver()
            >>> context = TypeContext(variables={"x": Type("number")})
            >>> solver.is_inhabitable(Type("number"), context)
            True
        """
        # Can inhabit if we can find a path from any available type
        # Start from "unknown" type (any available value)
        paths = self.find_paths(Type("unknown"), target, context, max_results=1)
        return len(paths) > 0

    # Private helper methods

    def _search(
        self,
        current: Type,
        target: Type,
        context: TypeContext,
        depth: int,
        visited: Set[str]
    ) -> List[InhabitationPath]:
        """
        Recursive search for inhabitation paths.

        Args:
            current: Current type in search
            target: Target type
            context: Type context
            depth: Current search depth
            visited: Set of visited type names (cycle detection)

        Returns:
            List of paths from current to target
        """
        # Base case: reached target
        if self._types_match(current, target):
            return [InhabitationPath([], current, target)]

        # Base case: max depth reached
        if depth >= self.max_depth:
            return []

        # Cycle detection
        if current.name in visited:
            return []

        # Generate possible operations from current type
        operations = self._generate_operations(current, context)

        paths = []
        new_visited = visited | {current.name}

        for op in operations:
            # Apply operation
            next_type = op.apply(current)

            # Prune if complexity grows too much
            if self._should_prune(next_type, target):
                continue

            # Recursive search from next type
            sub_paths = self._search(next_type, target, context, depth + 1, new_visited)

            # Prepend current operation to each sub-path
            for sub_path in sub_paths:
                path = InhabitationPath(
                    operations=[op] + sub_path.operations,
                    source=current,
                    target=target
                )
                paths.append(path)

        return paths

    def _generate_operations(
        self,
        current: Type,
        context: TypeContext
    ) -> List[Operation]:
        """
        Generate possible operations from current type.

        Args:
            current: Current type
            context: Type context

        Returns:
            List of applicable operations
        """
        operations = []

        # Special case: from "unknown" type, we can use any variable
        if current.name == "unknown":
            for var_name, var_type in context.variables.items():
                operations.append(Operation(
                    name=f"use {var_name}",
                    input_type=current,
                    output_type=var_type,
                    cost=0.0  # Direct variable access is free
                ))

        # Function applications
        for func_name, func_sig in context.functions.items():
            # Check if we can call this function with current type
            if func_sig.parameters:
                # For simplicity, only handle single-parameter functions
                if len(func_sig.parameters) == 1:
                    param_type = func_sig.parameters[0].type
                    if self._types_compatible(current, param_type):
                        operations.append(Operation(
                            name=f"call {func_name}",
                            input_type=param_type,
                            output_type=func_sig.return_type,
                            cost=1.0
                        ))

        # Property access
        if current.name in context.classes:
            class_type = context.classes[current.name]
            for prop_name, prop_type in class_type.properties.items():
                operations.append(Operation(
                    name=f"access {prop_name}",
                    input_type=current,
                    output_type=prop_type,
                    cost=0.5  # Property access is cheap
                ))

        if current.name in context.interfaces:
            interface_type = context.interfaces[current.name]
            for prop_name, prop_type in interface_type.properties.items():
                operations.append(Operation(
                    name=f"access {prop_name}",
                    input_type=current,
                    output_type=prop_type,
                    cost=0.5
                ))

        return operations

    def _types_match(self, type1: Type, type2: Type) -> bool:
        """
        Check if two types match for inhabitation purposes.

        Args:
            type1: First type
            type2: Second type

        Returns:
            True if types match
        """
        # Exact match
        if type1 == type2:
            return True

        # Ignore nullability for inhabitation
        if type1.name == type2.name and type1.parameters == type2.parameters:
            return True

        return False

    def _types_compatible(self, type1: Type, type2: Type) -> bool:
        """
        Check if type1 is compatible with type2 for operations.

        Args:
            type1: Source type
            type2: Target type

        Returns:
            True if compatible
        """
        # Same type
        if type1 == type2:
            return True

        # Same base type (ignore nullability)
        if type1.name == type2.name:
            return True

        # Unknown is compatible with anything
        if type1.name == "unknown" or type2.name == "unknown":
            return True

        return False

    def _should_prune(self, current: Type, target: Type) -> bool:
        """
        Heuristic to prune search space.

        Args:
            current: Current type in search
            target: Target type

        Returns:
            True if this branch should be pruned
        """
        # Prune if type complexity grows too much beyond target
        current_complexity = self._complexity(current)
        target_complexity = self._complexity(target)

        if current_complexity > target_complexity + 3:
            return True

        return False

    def _complexity(self, type: Type) -> int:
        """
        Estimate type complexity.

        Args:
            type: Type to measure

        Returns:
            Complexity score
        """
        complexity = 1

        # Add complexity for each type parameter
        for param in type.parameters:
            complexity += self._complexity(param)

        return complexity

    def _context_hash(self, context: TypeContext) -> int:
        """
        Generate hash for type context for caching.

        Args:
            context: Type context

        Returns:
            Hash value
        """
        # Hash based on available variables and functions
        var_items = tuple(sorted((k, str(v)) for k, v in context.variables.items()))
        func_items = tuple(sorted((k, str(v.return_type)) for k, v in context.functions.items()))

        return hash((var_items, func_items))

    def get_cache_stats(self) -> Dict[str, int]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache hits, misses, and size
        """
        return {
            "hits": self.cache_hits,
            "misses": self.cache_misses,
            "size": len(self.cache),
            "hit_rate": self.cache_hits / max(1, self.cache_hits + self.cache_misses)
        }

    def clear_cache(self) -> None:
        """Clear the path cache."""
        self.cache.clear()
        self.cache_hits = 0
        self.cache_misses = 0


# Re-export for cleaner imports
__all__ = [
    "Operation",
    "InhabitationPath",
    "InhabitationSolver",
]
