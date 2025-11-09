# Phase 3: Type System - Specification

## Overview

Implement type inhabitation solver, bidirectional type inference, and hole-driven generation to enable type-safe constrained code generation. This builds on Phase 2's syntactic constraints by adding type-level guarantees.

## Goals

1. **Correctness**: >75% reduction in type errors
2. **Performance**: <1ms type search with caching
3. **Coverage**: TypeScript first, then Rust/Haskell
4. **Integration**: Type constraints encoded in grammars

## Components

### 1. Type Inference Engine

**Purpose**: Bidirectional type inference for partial programs

**Key Features**:
- Forward pass: infer types from context
- Backward pass: refine types from usage
- Unification with constraint solving
- Support for generic/polymorphic types
- Gradual typing support (any/unknown)

**Interface**:
```python
class TypeInferenceEngine:
    def infer_expression(self, expr: AST, context: TypeContext) -> Type
    def check_expression(self, expr: AST, expected: Type, context: TypeContext) -> bool
    def infer_forward(self, node: AST, context: TypeContext) -> Type
    def infer_backward(self, node: AST, usage_type: Type, context: TypeContext) -> Type
    def unify(self, type1: Type, type2: Type) -> Optional[Dict[str, Type]]
```

**Performance Target**: <100μs per expression

### 2. Type Inhabitation Solver

**Purpose**: Find transformation paths from source to target types

**Algorithm**:
- Depth-limited search with memoization
- Pruning heuristics based on type complexity
- Cost-based path ranking
- Operation composition

**Operations**:
- Direct use (variable/function from context)
- Function application
- Property access
- Type coercion/conversion
- Generic instantiation

**Interface**:
```python
class InhabitationSolver:
    def find_paths(self, source: Type, target: Type, context: TypeContext) -> List[InhabitationPath]
    def find_best_path(self, source: Type, target: Type, context: TypeContext) -> Optional[InhabitationPath]
    def is_inhabitable(self, target: Type, context: TypeContext) -> bool
```

**Performance Target**: <1ms with caching, <5 iterations convergence

### 3. Hole-Driven Generation

**Purpose**: Generate code by filling typed holes under constraints

**Hole Types**:
- Expression holes: `/*__HOLE_expr__*/`
- Type holes: `/*__HOLE_type__*/`
- Statement holes: `/*__HOLE_stmt__*/`

**Process**:
1. Parse partial program with holes
2. Infer expected type for each hole
3. Generate grammar constrained by hole type
4. Fill hole with constrained decoding
5. Validate and iterate

**Interface**:
```python
class HoleFillingEngine:
    def identify_holes(self, code: str) -> List[Hole]
    def infer_hole_type(self, hole: Hole, context: TypeContext) -> Type
    def generate_grammar_for_hole(self, hole: Hole, hole_type: Type) -> str
    def fill_hole(self, hole: Hole, grammar: str) -> str
```

### 4. TypeScript Type System

**Purpose**: Language-specific type system for TypeScript

**Features**:
- Primitive types: string, number, boolean, null, undefined, void
- Structural types: objects, arrays, tuples
- Union and intersection types
- Literal types
- Generic types with constraints
- Function types with overloads
- Mapped types and conditional types (simplified)

**Integration**:
- Parse TypeScript type annotations
- Convert to Maze Type representation
- Export JSON Schema for validation
- Generate type-constrained grammars

**Interface**:
```python
class TypeScriptTypeSystem:
    def parse_type(self, type_annotation: str) -> Type
    def is_assignable(self, source: Type, target: Type) -> bool
    def widen_type(self, type: Type) -> Type
    def narrow_type(self, type: Type, guard: str) -> Type
    def infer_from_literal(self, literal: Any) -> Type
```

### 5. Type-to-Grammar Converter

**Purpose**: Encode type constraints into Lark grammars

**Strategy**:
- Generate grammar rules for each type
- Constrain terminals to type-valid values
- Embed JSON Schema for structured types
- Support union types via alternatives
- Handle generic types with templates

**Examples**:

**String type**:
```lark
string_expr: STRING | template_literal | string_concat
STRING: /"([^"\\]|\\.)*"/ | /'([^'\\]|\\.)*'/
```

**Number type**:
```lark
number_expr: NUMBER | arithmetic_expr
NUMBER: /[0-9]+(\.[0-9]+)?([eE][+-]?[0-9]+)?/
```

**Object type `{x: number, y: string}`**:
```lark
object_expr: "{" "x" ":" number_expr "," "y" ":" string_expr "}"
```

**Union type `string | number`**:
```lark
union_expr: string_expr | number_expr
```

**Interface**:
```python
class TypeToGrammarConverter:
    def convert(self, type: Type, context: TypeContext) -> str
    def convert_primitive(self, type: Type) -> str
    def convert_object(self, type: ClassType) -> str
    def convert_union(self, type: Type) -> str
    def convert_function(self, type: Type) -> str
```

## Dependencies

**Phase 2 (Complete)**:
- Grammar builder (GrammarBuilder, GrammarTemplate)
- JSON Schema synthesis (SchemaBuilder)
- Language templates (TypeScript, Python, Rust)

**External**:
- llguidance for grammar enforcement
- TypeScript compiler API for type checking (optional)
- pyright for Python type checking (future)

## Test Plan

### Unit Tests (Target: 80+ tests, 80%+ coverage)

1. **Type Inference** (15 tests)
   - Simple expressions
   - Function calls
   - Property access
   - Generic instantiation
   - Forward/backward inference
   - Unification

2. **Type Inhabitation** (15 tests)
   - Direct paths (variable lookup)
   - Function application paths
   - Property access paths
   - Multi-step paths
   - Pruning and optimization
   - Path ranking

3. **Hole Filling** (10 tests)
   - Hole identification
   - Type inference for holes
   - Grammar generation
   - Hole filling
   - Validation

4. **TypeScript Type System** (20 tests)
   - Primitive types
   - Object types
   - Union/intersection types
   - Generic types
   - Type assignability
   - Type widening/narrowing

5. **Type-to-Grammar** (20 tests)
   - Primitive conversions
   - Object conversions
   - Union conversions
   - Function conversions
   - Generic conversions
   - Integration with GrammarBuilder

6. **Integration Tests** (10 tests)
   - End-to-end hole filling
   - Type-constrained generation
   - Multi-hole programs
   - Error handling
   - Performance benchmarks

### Performance Tests

- Type inference: <100μs per expression
- Inhabitation search: <1ms with caching
- Hole type inference: <500μs
- Grammar generation: <5ms
- Full pipeline: <10ms per hole

### Coverage Targets

- Critical path (inference, inhabitation): 90%+
- Business logic (type system, grammar): 80%+
- Overall: 75%+

## Implementation Plan

### Subtasks (Dependency Order)

1. **maze-zih.3.1**: Type inference engine (bidirectional)
   - Core inference algorithm
   - Unification
   - Forward/backward passes
   - 15 tests

2. **maze-zih.3.2**: Type inhabitation solver
   - Search algorithm
   - Operations (apply, access, etc.)
   - Memoization and pruning
   - 15 tests

3. **maze-zih.3.3**: TypeScript type system
   - Type parsing
   - Assignability checking
   - Widening/narrowing
   - 20 tests

4. **maze-zih.3.4**: Type-to-grammar converter
   - Primitive conversions
   - Composite conversions
   - Integration with GrammarBuilder
   - 20 tests

5. **maze-zih.3.5**: Hole-driven generation engine
   - Hole identification
   - Type inference for holes
   - Grammar generation
   - Hole filling
   - 10 tests

6. **maze-zih.3.6**: Integration and optimization
   - End-to-end tests
   - Performance optimization
   - Caching layer
   - Documentation
   - 10 tests

### Parallelization Opportunities

**Stream A** (Type System Core):
- maze-zih.3.1 (inference)
- maze-zih.3.2 (inhabitation)

**Stream B** (Language Support):
- maze-zih.3.3 (TypeScript)

**Stream C** (Grammar Integration):
- maze-zih.3.4 (type-to-grammar)

**Sequential** (Integration):
- maze-zih.3.5 (hole filling) - depends on A + C
- maze-zih.3.6 (integration) - depends on all

## Typed Holes (Interfaces)

### TypeInferenceEngine ↔ InhabitationSolver
```python
# TypeInferenceEngine provides types for InhabitationSolver
inferred_type = inference_engine.infer_expression(expr, context)
paths = inhabitation_solver.find_paths(current_type, inferred_type, context)
```

### InhabitationSolver ↔ TypeToGrammarConverter
```python
# InhabitationSolver provides target type for grammar generation
target_type = path.target_type
grammar = grammar_converter.convert(target_type, context)
```

### HoleFillingEngine ↔ All Components
```python
# Orchestrates all components
hole_type = inference_engine.infer_hole_type(hole, context)
grammar = grammar_converter.convert(hole_type, context)
code = provider.generate(GenerationRequest(prompt=..., grammar=grammar))
```

## Edge Cases

1. **Circular type references**: Detect and break cycles
2. **Infinite inhabitation paths**: Max depth limits
3. **Ambiguous types**: Return all valid paths, rank by cost
4. **Missing context**: Graceful degradation to syntactic constraints
5. **Type errors**: Return diagnostics with suggestions
6. **Performance degradation**: Cache invalidation, LRU eviction

## Success Criteria

- [ ] All subtasks (maze-zih.3.1 through maze-zih.3.6) complete
- [ ] 80+ tests passing
- [ ] 75%+ test coverage
- [ ] Type inference <100μs per expression
- [ ] Inhabitation search <1ms with caching
- [ ] Integration tests demonstrate >75% type error reduction
- [ ] Documentation complete
- [ ] No TODO/FIXME/stub comments

## References

- **Type-Constrained Code Generation** (Mündler et al., 2025): prefix automata + type-inference search
- **Statically Contextualizing LLMs with Typed Holes** (Blinn et al., OOPSLA 2024): typed-hole scaffolding
- **Live Functional Programming with Typed Holes** (Omar et al., 2019): live bidirectional evaluation
- **OllamaHoles** (Tritlo): GHC plugin for hole filling
- **Hazel Project**: live bidirectional evaluation

## Phase Transition

**Entry Criteria** (from Phase 2):
- ✅ Grammar builder implemented
- ✅ Language templates complete
- ✅ JSON Schema synthesis working
- ✅ Provider adapters functional

**Exit Criteria** (to Phase 4):
- [ ] Type inference engine complete
- [ ] Inhabitation solver working
- [ ] Hole-driven generation functional
- [ ] TypeScript type system integrated
- [ ] Performance targets met
- [ ] All tests passing
