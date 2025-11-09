# Phase 3: Type System - Full Specification

## Component Decomposition

### 1. Type Inference Engine (`src/maze/type_system/inference.py`)

**Dependencies**:
- `src/maze/core/types.py` (Type, TypeContext, FunctionSignature)

**Interfaces**:
```python
@dataclass
class InferenceResult:
    """Result of type inference."""
    inferred_type: Type
    constraints: List[TypeConstraint]
    confidence: float  # 0.0-1.0

@dataclass
class TypeConstraint:
    """Constraint on type variables."""
    variable: str
    constraint_type: Literal["subtype", "supertype", "equals"]
    bound: Type

class TypeInferenceEngine:
    """Bidirectional type inference engine."""

    def infer_expression(self, expr: AST, context: TypeContext) -> InferenceResult:
        """Infer type of expression from context."""

    def check_expression(self, expr: AST, expected: Type, context: TypeContext) -> bool:
        """Check if expression has expected type."""

    def infer_forward(self, node: AST, context: TypeContext) -> Type:
        """Forward pass: infer from context."""

    def infer_backward(self, node: AST, usage_type: Type, context: TypeContext) -> Type:
        """Backward pass: refine from usage."""

    def unify(self, type1: Type, type2: Type) -> Optional[Dict[str, Type]]:
        """Unify two types, returning substitution if possible."""

    def apply_substitution(self, type: Type, subst: Dict[str, Type]) -> Type:
        """Apply type variable substitution."""
```

**Test Coverage**:
- Simple literals (number, string, boolean)
- Variable references
- Function calls
- Property access
- Array/object literals
- Generic instantiation
- Forward inference
- Backward inference
- Unification (success and failure cases)
- Constraint solving

### 2. Type Inhabitation Solver (`src/maze/type_system/inhabitation.py`)

**Dependencies**:
- `src/maze/core/types.py` (Type, TypeContext)
- `src/maze/type_system/inference.py` (TypeInferenceEngine)

**Interfaces**:
```python
@dataclass
class Operation:
    """Type transformation operation."""
    name: str
    input_type: Type
    output_type: Type
    cost: float

    def applicable(self, type: Type) -> bool:
        """Check if operation can apply to type."""

    def apply(self, type: Type) -> Type:
        """Apply operation to type."""

@dataclass
class InhabitationPath:
    """Sequence of operations to reach target type."""
    operations: List[Operation]
    source: Type
    target: Type

    @property
    def cost(self) -> float:
        """Total cost of path."""
        return sum(op.cost for op in self.operations)

    def to_code(self, source_expr: str) -> str:
        """Convert path to code."""

class InhabitationSolver:
    """Solver for type inhabitation problems."""

    def __init__(self, max_depth: int = 5, cache_size: int = 1000):
        self.max_depth = max_depth
        self.cache: Dict[Tuple[Type, Type], List[InhabitationPath]] = {}

    def find_paths(
        self,
        source: Type,
        target: Type,
        context: TypeContext,
        max_results: int = 10
    ) -> List[InhabitationPath]:
        """Find all inhabitation paths from source to target."""

    def find_best_path(
        self,
        source: Type,
        target: Type,
        context: TypeContext
    ) -> Optional[InhabitationPath]:
        """Find lowest-cost inhabitation path."""

    def is_inhabitable(self, target: Type, context: TypeContext) -> bool:
        """Check if target type can be inhabited from context."""
```

**Test Coverage**:
- Direct paths (variable exists with target type)
- Function application paths
- Property access paths
- Type coercion paths
- Multi-step composition
- Pruning effectiveness
- Caching behavior
- Performance (memoization)
- Path ranking by cost
- Edge cases (cycles, infinite loops)

### 3. TypeScript Type System (`src/maze/type_system/languages/typescript.py`)

**Dependencies**:
- `src/maze/core/types.py` (Type, ClassType, InterfaceType)

**Interfaces**:
```python
class TypeScriptTypeSystem:
    """TypeScript-specific type system."""

    def parse_type(self, type_annotation: str) -> Type:
        """Parse TypeScript type annotation to Maze Type."""

    def is_assignable(self, source: Type, target: Type) -> bool:
        """Check if source is assignable to target."""

    def widen_type(self, type: Type) -> Type:
        """Widen literal types to their base types."""

    def narrow_type(self, type: Type, guard: str) -> Type:
        """Narrow type based on type guard."""

    def infer_from_literal(self, literal: Any) -> Type:
        """Infer type from JavaScript literal."""

    def resolve_union(self, types: List[Type]) -> Type:
        """Create union type, simplifying if possible."""

    def resolve_intersection(self, types: List[Type]) -> Type:
        """Create intersection type, merging if possible."""

    def instantiate_generic(
        self,
        generic: Type,
        type_args: List[Type]
    ) -> Type:
        """Instantiate generic type with type arguments."""
```

**Test Coverage**:
- Parse primitive types
- Parse object types
- Parse array types
- Parse union types
- Parse intersection types
- Parse generic types
- Parse function types
- Assignability (subtyping)
- Type widening
- Type narrowing
- Literal type inference
- Union/intersection simplification
- Generic instantiation

### 4. Type-to-Grammar Converter (`src/maze/type_system/grammar_converter.py`)

**Dependencies**:
- `src/maze/core/types.py` (Type, ClassType, FunctionSignature)
- `src/maze/synthesis/grammar_builder.py` (GrammarBuilder)

**Interfaces**:
```python
class TypeToGrammarConverter:
    """Convert types to Lark grammars."""

    def __init__(self, language: str = "typescript"):
        self.language = language
        self.builder = GrammarBuilder()

    def convert(self, type: Type, context: TypeContext) -> str:
        """Convert type to grammar."""

    def convert_primitive(self, type: Type) -> str:
        """Convert primitive type to grammar."""

    def convert_object(self, class_type: ClassType, context: TypeContext) -> str:
        """Convert object type to grammar."""

    def convert_array(self, element_type: Type, context: TypeContext) -> str:
        """Convert array type to grammar."""

    def convert_union(self, types: List[Type], context: TypeContext) -> str:
        """Convert union type to grammar (alternatives)."""

    def convert_function(self, signature: FunctionSignature, context: TypeContext) -> str:
        """Convert function type to grammar."""

    def convert_generic(self, type: Type, context: TypeContext) -> str:
        """Convert generic type to grammar."""
```

**Test Coverage**:
- Primitive conversions (string, number, boolean)
- Object conversions
- Array conversions
- Union conversions (alternatives)
- Intersection conversions (merged rules)
- Function conversions
- Generic conversions
- Nullable type handling
- Nested types
- Integration with GrammarBuilder
- Grammar validation

### 5. Hole Filling Engine (`src/maze/type_system/holes.py`)

**Dependencies**:
- `src/maze/core/types.py` (Type, TypeContext)
- `src/maze/type_system/inference.py` (TypeInferenceEngine)
- `src/maze/type_system/grammar_converter.py` (TypeToGrammarConverter)
- `src/maze/orchestrator/providers` (ProviderAdapter)

**Interfaces**:
```python
@dataclass
class Hole:
    """Typed hole in code."""
    name: str
    location: Tuple[int, int]  # (line, column)
    expected_type: Optional[Type]
    context: TypeContext
    kind: Literal["expression", "statement", "type"]

@dataclass
class HoleFillResult:
    """Result of filling a hole."""
    hole: Hole
    filled_code: str
    inferred_type: Type
    grammar_used: str
    success: bool
    attempts: int

class HoleFillingEngine:
    """Engine for hole-driven code generation."""

    def __init__(
        self,
        inference_engine: TypeInferenceEngine,
        grammar_converter: TypeToGrammarConverter,
        provider: ProviderAdapter
    ):
        self.inference = inference_engine
        self.converter = grammar_converter
        self.provider = provider

    def identify_holes(self, code: str) -> List[Hole]:
        """Identify typed holes in code."""

    def infer_hole_type(self, hole: Hole, context: TypeContext) -> Type:
        """Infer expected type for hole."""

    def generate_grammar_for_hole(self, hole: Hole, hole_type: Type) -> str:
        """Generate grammar constrained by hole type."""

    def fill_hole(self, hole: Hole, max_attempts: int = 3) -> HoleFillResult:
        """Fill hole with type-constrained generation."""

    def fill_all_holes(
        self,
        code: str,
        context: TypeContext
    ) -> Tuple[str, List[HoleFillResult]]:
        """Fill all holes in code."""
```

**Test Coverage**:
- Hole identification (regex patterns)
- Expression holes
- Statement holes
- Type holes
- Type inference for holes
- Grammar generation
- Single hole filling
- Multiple hole filling
- Validation after filling
- Error handling
- Integration test

### 6. Integration Layer (`src/maze/type_system/__init__.py`)

**Dependencies**: All above components

**Interfaces**:
```python
class TypeSystemOrchestrator:
    """Orchestrator for type-directed code generation."""

    def __init__(self, language: str = "typescript"):
        self.language = language
        self.inference = TypeInferenceEngine()
        self.inhabitation = InhabitationSolver()
        self.type_system = TypeScriptTypeSystem()
        self.converter = TypeToGrammarConverter(language)

    def generate_with_type_constraints(
        self,
        prompt: str,
        context: TypeContext,
        expected_type: Optional[Type] = None,
        provider: Optional[ProviderAdapter] = None
    ) -> GenerationResult:
        """Generate code with type constraints."""
```

## Dependency Graph

```
Core Types (maze.core.types)
    │
    ├─→ Type Inference Engine (maze.type_system.inference)
    │       │
    │       ├─→ Inhabitation Solver (maze.type_system.inhabitation)
    │       │
    │       └─→ Hole Filling Engine (maze.type_system.holes)
    │               │
    │               └─→ Type-to-Grammar Converter (maze.type_system.grammar_converter)
    │                       │
    │                       └─→ Grammar Builder (maze.synthesis.grammar_builder)
    │
    └─→ TypeScript Type System (maze.type_system.languages.typescript)
            │
            └─→ Type-to-Grammar Converter
```

## Test Plan (Detailed)

### Phase 3.1: Type Inference (15 tests)
```python
# tests/unit/test_type_system/test_inference.py

class TestTypeInference:
    def test_infer_literal_number(self)
    def test_infer_literal_string(self)
    def test_infer_literal_boolean(self)
    def test_infer_variable_from_context(self)
    def test_infer_function_call(self)
    def test_infer_property_access(self)
    def test_infer_array_literal(self)
    def test_infer_object_literal(self)
    def test_check_valid_type(self)
    def test_check_invalid_type(self)
    def test_unify_same_types(self)
    def test_unify_generic_types(self)
    def test_unify_incompatible_types(self)
    def test_forward_inference(self)
    def test_backward_inference(self)
```

### Phase 3.2: Type Inhabitation (15 tests)
```python
# tests/unit/test_type_system/test_inhabitation.py

class TestInhabitationSolver:
    def test_direct_path_variable_exists(self)
    def test_function_application_path(self)
    def test_property_access_path(self)
    def test_multi_step_path(self)
    def test_no_path_exists(self)
    def test_path_cost_calculation(self)
    def test_path_ranking(self)
    def test_pruning_deep_paths(self)
    def test_caching_paths(self)
    def test_cycle_detection(self)
    def test_max_depth_limit(self)
    def test_path_to_code_conversion(self)
    def test_is_inhabitable_true(self)
    def test_is_inhabitable_false(self)
    def test_find_best_path(self)
```

### Phase 3.3: TypeScript Type System (20 tests)
```python
# tests/unit/test_type_system/test_typescript.py

class TestTypeScriptTypeSystem:
    def test_parse_primitive_string(self)
    def test_parse_primitive_number(self)
    def test_parse_object_type(self)
    def test_parse_array_type(self)
    def test_parse_union_type(self)
    def test_parse_intersection_type(self)
    def test_parse_generic_type(self)
    def test_parse_function_type(self)
    def test_assignability_primitives(self)
    def test_assignability_objects(self)
    def test_assignability_unions(self)
    def test_widen_literal_to_primitive(self)
    def test_narrow_union_type(self)
    def test_infer_from_number_literal(self)
    def test_infer_from_string_literal(self)
    def test_resolve_union_simplify(self)
    def test_resolve_intersection_merge(self)
    def test_instantiate_generic_array(self)
    def test_instantiate_generic_map(self)
    def test_complex_nested_types(self)
```

### Phase 3.4: Type-to-Grammar (20 tests)
```python
# tests/unit/test_type_system/test_grammar_converter.py

class TestTypeToGrammarConverter:
    def test_convert_string_primitive(self)
    def test_convert_number_primitive(self)
    def test_convert_boolean_primitive(self)
    def test_convert_simple_object(self)
    def test_convert_nested_object(self)
    def test_convert_array(self)
    def test_convert_tuple(self)
    def test_convert_union(self)
    def test_convert_intersection(self)
    def test_convert_function_type(self)
    def test_convert_generic_array(self)
    def test_convert_nullable_type(self)
    def test_convert_optional_property(self)
    def test_convert_literal_type(self)
    def test_grammar_validates_valid_input(self)
    def test_grammar_rejects_invalid_input(self)
    def test_integration_with_grammar_builder(self)
    def test_complex_nested_types(self)
    def test_recursive_types(self)
    def test_grammar_deduplication(self)
```

### Phase 3.5: Hole Filling (10 tests)
```python
# tests/unit/test_type_system/test_holes.py

class TestHoleFillingEngine:
    def test_identify_expression_hole(self)
    def test_identify_multiple_holes(self)
    def test_infer_hole_type_from_context(self)
    def test_generate_grammar_for_hole(self)
    def test_fill_simple_hole(self)
    def test_fill_all_holes(self)
    def test_hole_fill_validation(self)
    def test_retry_on_validation_failure(self)
    def test_max_attempts_exceeded(self)
    def test_end_to_end_hole_filling(self)
```

### Phase 3.6: Integration (10 tests)
```python
# tests/integration/test_type_system_integration.py

class TestTypeSystemIntegration:
    def test_typescript_simple_function(self)
    def test_typescript_with_imports(self)
    def test_typescript_generic_function(self)
    def test_multiple_holes_dependency(self)
    def test_type_error_recovery(self)
    def test_performance_inference(self)
    def test_performance_inhabitation(self)
    def test_performance_grammar_generation(self)
    def test_end_to_end_pipeline(self)
    def test_cache_effectiveness(self)
```

## Edge Cases and Invariants

### Invariants
1. Type inference always returns a type (may be "unknown")
2. Inhabitation search terminates (max depth limit)
3. Grammars are valid Lark syntax
4. Filled holes are syntactically valid
5. Cache never grows unbounded (LRU eviction)

### Edge Cases
1. **Circular type references**: Detect cycles, return error
2. **Infinite inhabitation paths**: Max depth limit (5)
3. **Ambiguous types**: Return all paths, rank by cost
4. **Missing context**: Degrade to syntactic constraints
5. **Type errors**: Return diagnostics with suggestions
6. **Empty context**: Use only builtin types
7. **Generic with no constraints**: Instantiate with "unknown"
8. **Union with duplicate types**: Simplify
9. **Intersection of incompatible types**: Return "never"
10. **Nullable in strict mode**: Preserve null in union

## Constraints and Assumptions

### Constraints
- TypeScript first (Python/Rust later)
- Simplified generic handling (no variance)
- No conditional types (yet)
- No mapped types (yet)
- Structural typing only (no nominal)

### Assumptions
- Code is parseable (AST available)
- Context is complete (all symbols known)
- Provider supports grammar constraints
- LLGuidance is available for enforcement

## Traceability

| Requirement | Component | Tests | Metrics |
|-------------|-----------|-------|---------|
| Bidirectional inference | TypeInferenceEngine | test_inference.py (15) | <100μs/expr |
| Type inhabitation | InhabitationSolver | test_inhabitation.py (15) | <1ms cached |
| TypeScript support | TypeScriptTypeSystem | test_typescript.py (20) | Full coverage |
| Type-to-grammar | TypeToGrammarConverter | test_grammar_converter.py (20) | <5ms |
| Hole filling | HoleFillingEngine | test_holes.py (10) | <10ms/hole |
| Integration | TypeSystemOrchestrator | test_integration.py (10) | >75% error reduction |

## Success Metrics

### Quantitative
- [ ] 90+ tests passing
- [ ] 80%+ code coverage
- [ ] Type inference <100μs per expression
- [ ] Inhabitation search <1ms with caching
- [ ] Grammar generation <5ms per type
- [ ] Hole filling <10ms per hole
- [ ] >75% type error reduction vs unconstrained

### Qualitative
- [ ] Clean separation of concerns
- [ ] Well-documented APIs
- [ ] No circular dependencies
- [ ] Comprehensive error messages
- [ ] Debuggable (logging at key points)
- [ ] Extensible (easy to add languages)
