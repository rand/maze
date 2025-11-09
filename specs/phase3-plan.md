# Phase 3: Type System - Execution Plan

## Critical Path

The critical path determines the minimum time to complete Phase 3:

1. **maze-zih.3.1**: Type Inference Engine (3-4 hours)
   - Core algorithm implementation
   - Bidirectional inference
   - Unification
   - 15 tests
   - **Blocks**: maze-zih.3.2, maze-zih.3.5

2. **maze-zih.3.2**: Type Inhabitation Solver (3-4 hours)
   - Search algorithm
   - Operations and paths
   - Memoization
   - 15 tests
   - **Blocks**: maze-zih.3.5

3. **maze-zih.3.4**: Type-to-Grammar Converter (2-3 hours)
   - Primitive conversions
   - Composite conversions
   - GrammarBuilder integration
   - 20 tests
   - **Blocks**: maze-zih.3.5

4. **maze-zih.3.5**: Hole Filling Engine (2-3 hours)
   - Hole identification
   - Grammar generation
   - Integration
   - 10 tests
   - **Blocks**: maze-zih.3.6

5. **maze-zih.3.6**: Integration & Optimization (2-3 hours)
   - End-to-end tests
   - Performance optimization
   - Documentation
   - 10 tests

**Total Critical Path Time**: 12-17 hours

## Parallel Streams

### Stream A: Type System Core (Sequential)
**Tasks**: maze-zih.3.1 → maze-zih.3.2

**Justification**: InhabitationSolver depends on TypeInferenceEngine for type checking during path search.

**Timeline**:
- maze-zih.3.1: 3-4 hours
- maze-zih.3.2: 3-4 hours
- **Total**: 6-8 hours

### Stream B: Language Support (Independent)
**Tasks**: maze-zih.3.3 (TypeScript Type System)

**Justification**: Can develop in parallel with core type system. Only integrates at grammar conversion stage.

**Timeline**:
- maze-zih.3.3: 3-4 hours
- **Total**: 3-4 hours

**Can run concurrently with**: Stream A (maze-zih.3.1 + maze-zih.3.2)

### Stream C: Grammar Integration (Independent initially)
**Tasks**: maze-zih.3.4 (Type-to-Grammar Converter)

**Justification**: Needs TypeScript type system (maze-zih.3.3) for language-specific conversions, but can start basic framework in parallel.

**Timeline**:
- maze-zih.3.4 (basic framework): 1 hour (parallel)
- maze-zih.3.4 (TypeScript integration): 2-3 hours (after maze-zih.3.3)
- **Total**: 3-4 hours

**Can run concurrently with**: Stream A initially, then depends on Stream B

### Stream D: Integration (Sequential, after all streams)
**Tasks**: maze-zih.3.5 → maze-zih.3.6

**Justification**: Requires all components complete.

**Dependencies**:
- maze-zih.3.5 depends on: A (inference + inhabitation) + C (grammar conversion)
- maze-zih.3.6 depends on: All previous tasks

**Timeline**:
- maze-zih.3.5: 2-3 hours
- maze-zih.3.6: 2-3 hours
- **Total**: 4-6 hours

## Optimized Execution Schedule

### Phase 1: Parallel Foundation (3-4 hours)
**Concurrent**:
- **Stream A**: Start maze-zih.3.1 (Type Inference Engine)
- **Stream B**: Start maze-zih.3.3 (TypeScript Type System)
- **Stream C**: Start maze-zih.3.4 (basic framework)

**Deliverables**:
- TypeInferenceEngine with core inference
- TypeScriptTypeSystem with type parsing
- TypeToGrammarConverter basic structure

### Phase 2: Core Completion (3-4 hours)
**Concurrent**:
- **Stream A**: maze-zih.3.2 (InhabitationSolver)
- **Stream C**: maze-zih.3.4 (TypeScript integration)

**Dependencies**:
- maze-zih.3.2 requires maze-zih.3.1 complete
- maze-zih.3.4 full requires maze-zih.3.3 complete

**Deliverables**:
- InhabitationSolver fully tested
- TypeToGrammarConverter with TypeScript support

### Phase 3: Integration (2-3 hours)
**Sequential**:
- maze-zih.3.5 (Hole Filling Engine)

**Dependencies**:
- Requires maze-zih.3.1, maze-zih.3.2, maze-zih.3.4 complete

**Deliverables**:
- HoleFillingEngine with end-to-end hole filling

### Phase 4: Finalization (2-3 hours)
**Sequential**:
- maze-zih.3.6 (Integration & Optimization)

**Dependencies**:
- Requires all previous tasks complete

**Deliverables**:
- TypeSystemOrchestrator
- Performance benchmarks
- Complete documentation

## Total Timeline

**With full parallelization**: 10-14 hours
**Conservative estimate**: 12-16 hours

## Task Details

### maze-zih.3.1: Type Inference Engine
**File**: `src/maze/type_system/inference.py`
**Tests**: `tests/unit/test_type_system/test_inference.py`

**Implementation Steps**:
1. Create `InferenceResult` and `TypeConstraint` dataclasses
2. Implement `TypeInferenceEngine` class
3. Implement `infer_expression()` with pattern matching
4. Implement `check_expression()` validation
5. Implement `infer_forward()` context-based inference
6. Implement `infer_backward()` usage-based inference
7. Implement `unify()` type unification
8. Write 15 tests covering all cases
9. Achieve 90%+ coverage

**Acceptance Criteria**:
- [ ] All 15 tests passing
- [ ] <100μs per expression benchmark
- [ ] 90%+ code coverage
- [ ] Documentation complete

### maze-zih.3.2: Type Inhabitation Solver
**File**: `src/maze/type_system/inhabitation.py`
**Tests**: `tests/unit/test_type_system/test_inhabitation.py`

**Implementation Steps**:
1. Create `Operation` and `InhabitationPath` dataclasses
2. Implement `InhabitationSolver` class with cache
3. Implement `find_paths()` with memoization
4. Implement `_search()` recursive algorithm
5. Implement pruning heuristics
6. Implement path ranking by cost
7. Implement `find_best_path()` optimization
8. Write 15 tests covering all cases
9. Achieve 90%+ coverage

**Acceptance Criteria**:
- [ ] All 15 tests passing
- [ ] <1ms with caching benchmark
- [ ] Cache hit rate >70%
- [ ] 90%+ code coverage
- [ ] Documentation complete

### maze-zih.3.3: TypeScript Type System
**File**: `src/maze/type_system/languages/typescript.py`
**Tests**: `tests/unit/test_type_system/test_typescript.py`

**Implementation Steps**:
1. Create `TypeScriptTypeSystem` class
2. Implement `parse_type()` for all TS types
3. Implement `is_assignable()` subtyping rules
4. Implement `widen_type()` and `narrow_type()`
5. Implement `infer_from_literal()`
6. Implement union/intersection resolution
7. Implement generic instantiation
8. Write 20 tests covering all features
9. Achieve 85%+ coverage

**Acceptance Criteria**:
- [ ] All 20 tests passing
- [ ] Handles all common TS types
- [ ] Correct assignability rules
- [ ] 85%+ code coverage
- [ ] Documentation complete

### maze-zih.3.4: Type-to-Grammar Converter
**File**: `src/maze/type_system/grammar_converter.py`
**Tests**: `tests/unit/test_type_system/test_grammar_converter.py`

**Implementation Steps**:
1. Create `TypeToGrammarConverter` class
2. Implement `convert()` dispatcher
3. Implement `convert_primitive()` for all primitives
4. Implement `convert_object()` with property rules
5. Implement `convert_array()` with element constraints
6. Implement `convert_union()` with alternatives
7. Implement `convert_function()` signatures
8. Integrate with `GrammarBuilder`
9. Write 20 tests including integration tests
10. Achieve 85%+ coverage

**Acceptance Criteria**:
- [ ] All 20 tests passing
- [ ] Generated grammars validate correctly
- [ ] <5ms grammar generation
- [ ] Integration with GrammarBuilder working
- [ ] 85%+ code coverage
- [ ] Documentation complete

### maze-zih.3.5: Hole Filling Engine
**File**: `src/maze/type_system/holes.py`
**Tests**: `tests/unit/test_type_system/test_holes.py`

**Implementation Steps**:
1. Create `Hole` and `HoleFillResult` dataclasses
2. Implement `HoleFillingEngine` class
3. Implement `identify_holes()` regex patterns
4. Implement `infer_hole_type()` using TypeInferenceEngine
5. Implement `generate_grammar_for_hole()` integration
6. Implement `fill_hole()` with retry logic
7. Implement `fill_all_holes()` orchestration
8. Write 10 tests including end-to-end
9. Achieve 80%+ coverage

**Acceptance Criteria**:
- [ ] All 10 tests passing
- [ ] <10ms per hole benchmark
- [ ] Retry logic works correctly
- [ ] Integration test demonstrates value
- [ ] 80%+ code coverage
- [ ] Documentation complete

### maze-zih.3.6: Integration & Optimization
**File**: `src/maze/type_system/__init__.py`
**Tests**: `tests/integration/test_type_system_integration.py`

**Implementation Steps**:
1. Create `TypeSystemOrchestrator` class
2. Implement `generate_with_type_constraints()`
3. Write 10 integration tests
4. Run performance benchmarks
5. Optimize hot paths (caching, memoization)
6. Add comprehensive logging
7. Write API documentation
8. Create usage examples
9. Verify all performance targets met

**Acceptance Criteria**:
- [ ] All 10 integration tests passing
- [ ] All performance targets met
- [ ] >75% type error reduction demonstrated
- [ ] Complete API documentation
- [ ] Usage examples working
- [ ] No TODO/FIXME comments

## Dependencies (Beads Notation)

```
maze-zih.3.1 (inference)
    ├─→ maze-zih.3.2 (inhabitation) [blocks]
    └─→ maze-zih.3.5 (holes) [blocks]

maze-zih.3.3 (typescript)
    └─→ maze-zih.3.4 (grammar converter) [blocks]

maze-zih.3.2 (inhabitation)
    └─→ maze-zih.3.5 (holes) [blocks]

maze-zih.3.4 (grammar converter)
    └─→ maze-zih.3.5 (holes) [blocks]

maze-zih.3.5 (holes)
    └─→ maze-zih.3.6 (integration) [blocks]
```

## Risk Mitigation

### Risk 1: Type Inference Complexity
**Risk**: Bidirectional inference harder than expected
**Mitigation**: Start with simple forward inference, add backward later
**Contingency**: Simplify to forward-only if needed

### Risk 2: Inhabitation Search Performance
**Risk**: Search too slow without aggressive caching
**Mitigation**: Implement caching from start, add pruning heuristics
**Contingency**: Reduce max_depth from 5 to 3

### Risk 3: TypeScript Type Parsing
**Risk**: TS type syntax is complex and evolving
**Mitigation**: Focus on common subset (primitives, objects, arrays, unions)
**Contingency**: Use regex-based parsing instead of full grammar

### Risk 4: Grammar Generation Quality
**Risk**: Generated grammars too loose or too strict
**Mitigation**: Write comprehensive tests with real examples
**Contingency**: Add manual override mechanism for problem cases

### Risk 5: Integration Issues
**Risk**: Components don't work together smoothly
**Mitigation**: Define clear interfaces upfront, write integration tests early
**Contingency**: Add adapter layers to bridge incompatibilities

## Validation Checklist

Before marking each task complete:
- [ ] All tests passing
- [ ] Code coverage target met
- [ ] Performance benchmark met
- [ ] Documentation written
- [ ] No TODO/FIXME/stub comments
- [ ] Code committed
- [ ] Integration test with downstream components (if applicable)

Before marking Phase 3 complete:
- [ ] All 90+ tests passing
- [ ] 80%+ overall coverage
- [ ] All performance targets met
- [ ] Integration test demonstrates >75% type error reduction
- [ ] API documentation complete
- [ ] Usage examples working
- [ ] No blocking issues

## Rollout Strategy

1. **Commit after each task**: Allows reverting if needed
2. **Test before committing**: Ensure stability
3. **Update documentation**: Keep it current
4. **Update Beads issues**: Track progress
5. **Performance profiling**: After maze-zih.3.6 complete

## Next Steps After Phase 3

Once Phase 3 is complete:
1. Close all maze-zih.3.x issues
2. Close maze-zih.3 parent issue
3. Commit phase3-*.md specs for documentation
4. Prepare for Phase 4 (Validation & Repair)
5. Celebrate! 🎉 (but skip the emoji in actual commits)
