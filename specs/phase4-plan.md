# Phase 4: Validation & Repair - Execution Plan

## Critical Path

**Total Estimated Time**: 16-22 hours

**Critical Sequence** (longest dependency chain):
1. Component 4.1: SyntaxValidator (2-3h)
2. Component 4.2: TypeValidator (2-3h, depends on 4.1)
3. Component 4.3: TestValidator + RUNE integration (3-4h, depends on 4.5)
4. Component 4.5: RuneExecutor (2-3h)
5. Component 4.6: RepairOrchestrator (3-4h, depends on all validators)
6. Component 4.8: ValidationPipeline (2-3h, depends on all validators)
7. Integration tests (2-3h, depends on everything)

**Critical Path Duration**: ~16-20 hours

## Parallel Execution Streams

### Stream A: Validators (can run in parallel)
```
┌─ 4.1: SyntaxValidator (2-3h)
├─ 4.4: LintValidator (2-3h)
└─ 4.7: PedanticRavenIntegration (2-3h)
```
**Stream A Duration**: 2-3 hours (parallel)

### Stream B: Sandbox
```
└─ 4.5: RuneExecutor (2-3h)
```
**Stream B Duration**: 2-3 hours (can run parallel with Stream A)

### Stream C: Type Validation (depends on Phase 3)
```
└─ 4.2: TypeValidator (2-3h, after 4.1)
```
**Stream C Duration**: 2-3 hours (can start after 4.1)

### Stream D: Test Validation (depends on RUNE)
```
└─ 4.3: TestValidator (2-3h, after 4.5)
```
**Stream D Duration**: 2-3 hours (after Stream B)

### Stream E: Orchestration (depends on A, B, C, D)
```
├─ 4.6: RepairOrchestrator (3-4h)
└─ 4.8: ValidationPipeline (2-3h, can run parallel with 4.6)
```
**Stream E Duration**: 3-4 hours (after A, B, C, D complete)

### Stream F: Integration (depends on E)
```
└─ Integration tests and optimization (2-3h)
```

## Task Breakdown

### Task 4.1: SyntaxValidator
**Estimated Time**: 2-3 hours
**Priority**: High (critical path)
**Dependencies**: None

**Subtasks**:
1. Implement SyntaxValidator class (30min)
2. Integrate tree-sitter parsers (45min)
3. Add language-specific fallbacks (45min)
   - TypeScript: tsc
   - Python: ast.parse + pyright
   - Rust: cargo check
   - Go: go build
   - Zig: zig ast-check
4. Implement error extraction (30min)
5. Add suggested fix generation (30min)
6. Implement caching (20min)
7. Write 20 unit tests (1h)

**Deliverables**:
- `src/maze/validation/syntax.py` (~350 lines)
- `tests/unit/test_validation/test_syntax.py` (20 tests)
- All tests passing

**Success Criteria**:
- Parse valid code in 5 languages
- Detect and locate syntax errors
- Suggest fixes for common errors
- <50ms performance on 1000-line files

---

### Task 4.2: TypeValidator
**Estimated Time**: 2-3 hours
**Priority**: High (critical path)
**Dependencies**: 4.1 (SyntaxValidator), Phase 3 (Type System)

**Subtasks**:
1. Implement TypeValidator class (30min)
2. Integrate Phase 3 TypeScript type system (30min)
3. Add pyright integration for Python (30min)
4. Add rust-analyzer integration for Rust (30min)
5. Add go build type checking (20min)
6. Add zig type checking (20min)
7. Implement error parsing (30min)
8. Add suggested fix generation (30min)
9. Write 20 unit tests (1h)

**Deliverables**:
- `src/maze/validation/types.py` (~400 lines)
- `tests/unit/test_validation/test_types.py` (20 tests)
- Integration with Phase 3 type system
- All tests passing

**Success Criteria**:
- Detect type mismatches in 5 languages
- Parse type checker output correctly
- Suggest type annotations/casts
- <200ms performance on 500-line files

---

### Task 4.3: TestValidator
**Estimated Time**: 2-3 hours
**Priority**: High (critical path)
**Dependencies**: 4.5 (RuneExecutor)

**Subtasks**:
1. Implement TestValidator class (30min)
2. Integrate RUNE sandbox (30min)
3. Add pytest runner and parser (30min)
4. Add jest/vitest runner and parser (30min)
5. Add cargo test runner and parser (30min)
6. Add go test runner and parser (20min)
7. Add zig test runner and parser (20min)
8. Implement test result extraction (30min)
9. Write 15 unit tests (1h)

**Deliverables**:
- `src/maze/validation/tests.py` (~350 lines)
- `tests/unit/test_validation/test_tests.py` (15 tests)
- All tests passing

**Success Criteria**:
- Execute tests in 5 languages
- Parse test framework output
- Extract test failures with locations
- Enforce timeouts and resource limits

---

### Task 4.4: LintValidator
**Estimated Time**: 2-3 hours
**Priority**: Medium (not critical path)
**Dependencies**: None (parallel with 4.1)

**Subtasks**:
1. Implement LintValidator class (30min)
2. Integrate ruff for Python (30min)
3. Integrate eslint for TypeScript (30min)
4. Integrate clippy for Rust (30min)
5. Integrate golangci-lint for Go (20min)
6. Integrate zig fmt for Zig (20min)
7. Implement output parsing (30min)
8. Add auto-fix support (30min)
9. Implement caching (20min)
10. Write 10 unit tests (45min)

**Deliverables**:
- `src/maze/validation/lint.py` (~300 lines)
- `tests/unit/test_validation/test_lint.py` (10 tests)
- All tests passing

**Success Criteria**:
- Detect style violations in 5 languages
- Parse linter output correctly
- Apply auto-fixes where available
- <100ms performance

---

### Task 4.5: RuneExecutor
**Estimated Time**: 2-3 hours
**Priority**: High (blocks 4.3)
**Dependencies**: None (parallel with validators)

**Subtasks**:
1. Design RuneExecutor interface (20min)
2. Implement RUNE integration (1h)
   - Filesystem isolation
   - Network isolation
   - Resource limits (CPU, memory)
   - Process isolation
3. Add security violation detection (30min)
4. Implement resource usage tracking (30min)
5. Add cleanup mechanisms (20min)
6. Write 10 unit tests (1h)

**Deliverables**:
- `src/maze/integrations/rune/__init__.py` (~400 lines)
- `tests/unit/test_integrations/test_rune.py` (10 tests)
- All tests passing

**Success Criteria**:
- Execute code safely in sandbox
- Enforce all resource limits
- Detect security violations
- Clean up resources reliably

---

### Task 4.6: RepairOrchestrator
**Estimated Time**: 3-4 hours
**Priority**: High (critical path)
**Dependencies**: 4.1, 4.2, 4.3, 4.4, 4.8 (all validators), Phase 2 (Constraint Synthesis)

**Subtasks**:
1. Implement RepairOrchestrator class (45min)
2. Implement diagnostic analysis (1h)
   - Pattern extraction
   - Root cause identification
   - Severity classification
3. Implement strategy selection (45min)
   - Constraint tightening
   - Type narrowing
   - Example-based
   - Template fallback
4. Implement constraint refinement (1h)
   - Grammar modification
   - Type constraint adjustment
   - Example injection
5. Implement pattern learning (30min)
6. Add repair loop logic (30min)
7. Write 15 unit tests (1h)

**Deliverables**:
- `src/maze/repair/orchestrator.py` (~500 lines)
- `tests/unit/test_repair/test_orchestrator.py` (15 tests)
- All tests passing

**Success Criteria**:
- Analyze diagnostics accurately
- Select appropriate strategies
- Refine constraints effectively
- Learn from successful repairs
- Respect max attempts limit

---

### Task 4.7: PedanticRavenIntegration
**Estimated Time**: 2-3 hours
**Priority**: Medium (quality gate, not critical path)
**Dependencies**: None (parallel with validators)

**Subtasks**:
1. Implement PedanticRavenIntegration class (30min)
2. Add security scanning (1h)
   - SQL injection
   - XSS
   - Command injection
   - Path traversal
   - Hardcoded credentials
3. Add quality metrics (45min)
   - Cyclomatic complexity
   - Code duplication
   - Function length
4. Add performance pattern detection (30min)
5. Add documentation checking (30min)
6. Add coverage integration (20min)
7. Write 10 unit tests (1h)

**Deliverables**:
- `src/maze/integrations/pedantic_raven/__init__.py` (~450 lines)
- `tests/unit/test_integrations/test_pedantic_raven.py` (10 tests)
- All tests passing

**Success Criteria**:
- Detect security vulnerabilities
- Calculate quality metrics
- Identify performance anti-patterns
- Check documentation completeness

---

### Task 4.8: ValidationPipeline
**Estimated Time**: 2-3 hours
**Priority**: High (critical path)
**Dependencies**: 4.1, 4.2, 4.3, 4.4 (all validators)

**Subtasks**:
1. Implement ValidationPipeline class (30min)
2. Implement sequential validation flow (30min)
3. Add parallel validation support (30min)
4. Implement early exit logic (20min)
5. Add comprehensive diagnostic collection (30min)
6. Implement stage selection (20min)
7. Add performance tracking (20min)
8. Write 10 unit tests (1h)

**Deliverables**:
- `src/maze/validation/pipeline.py` (~300 lines)
- `tests/unit/test_validation/test_pipeline.py` (10 tests)
- All tests passing

**Success Criteria**:
- Run all validators in order
- Support parallel execution
- Early exit on success
- Collect comprehensive diagnostics
- <500ms total (excluding tests)

---

### Task 4.9: Integration Tests
**Estimated Time**: 2-3 hours
**Priority**: High (quality assurance)
**Dependencies**: All components (4.1-4.8)

**Subtasks**:
1. End-to-end validation tests (1h, 10 tests)
   - Valid code across languages
   - Invalid code with diagnostics
   - Full pipeline with all stages
   - Performance targets
2. Repair loop integration tests (1h, 10 tests)
   - Syntax error repair
   - Type error repair
   - Test failure repair
   - Multi-stage repair
   - Constraint learning
3. Sandbox integration tests (30min, 5 tests)
   - RUNE with validators
   - Resource limits
   - Security enforcement

**Deliverables**:
- `tests/integration/test_validation_integration.py` (10 tests)
- `tests/integration/test_repair_integration.py` (10 tests)
- `tests/integration/test_sandbox_integration.py` (5 tests)
- All 25 tests passing

**Success Criteria**:
- Complete workflows tested
- All performance targets met
- All integration points validated

---

### Task 4.10: Optimization & Documentation
**Estimated Time**: 1-2 hours
**Priority**: Medium
**Dependencies**: 4.9 (all tests passing)

**Subtasks**:
1. Performance profiling (30min)
2. Optimization passes (30min)
3. Documentation review (30min)
4. Final integration testing (30min)

**Deliverables**:
- Performance targets met
- Documentation complete
- All 115+ tests passing

---

## Dependency Graph

```
                        ┌──────────────┐
                        │   Phase 1    │
                        │   Phase 2    │
                        │   Phase 3    │
                        └──────┬───────┘
                               │
                ┌──────────────┼──────────────┐
                │              │              │
           ┌────▼────┐    ┌───▼────┐    ┌───▼────┐
           │   4.1   │    │  4.4   │    │  4.5   │
           │ Syntax  │    │  Lint  │    │  RUNE  │
           └────┬────┘    └────┬───┘    └───┬────┘
                │              │             │
           ┌────▼────┐         │        ┌───▼────┐
           │   4.2   │         │        │  4.3   │
           │  Types  │         │        │ Tests  │
           └────┬────┘         │        └───┬────┘
                │              │             │
                └──────┬───────┴─────────────┘
                       │
                  ┌────▼────┐
                  │   4.8   │
                  │Pipeline │
                  └────┬────┘
                       │
                ┌──────┴───────┐
                │              │
           ┌────▼────┐    ┌───▼────┐
           │   4.6   │    │  4.7   │
           │ Repair  │    │ P.Raven│
           └────┬────┘    └───┬────┘
                │              │
                └──────┬───────┘
                       │
                  ┌────▼────┐
                  │   4.9   │
                  │  Tests  │
                  └────┬────┘
                       │
                  ┌────▼────┐
                  │  4.10   │
                  │  Polish │
                  └─────────┘
```

## Parallelization Strategy

**Phase 1: Foundation** (parallel)
- Start 4.1, 4.4, 4.5, 4.7 simultaneously
- Duration: 2-3 hours

**Phase 2: Dependent Components** (parallel after phase 1)
- Start 4.2 after 4.1 completes
- Start 4.3 after 4.5 completes
- Duration: 2-3 hours

**Phase 3: Integration** (sequential after phase 2)
- Start 4.8 after all validators complete
- Duration: 2-3 hours

**Phase 4: Orchestration** (parallel after phase 3)
- Start 4.6 and complete 4.7 simultaneously
- Duration: 3-4 hours

**Phase 5: Testing** (sequential after phase 4)
- Run 4.9 after all components complete
- Duration: 2-3 hours

**Phase 6: Polish** (sequential after phase 5)
- Run 4.10 after tests pass
- Duration: 1-2 hours

**Total Parallel Duration**: ~12-16 hours (vs 22-25 hours sequential)

## Risk Mitigation

### Risk: RUNE integration complexity
**Likelihood**: Medium
**Impact**: High (blocks test validation)
**Mitigation**:
- Start 4.5 early (parallel with validators)
- Have fallback: run tests unsandboxed for development
- Document RUNE requirements clearly

### Risk: Language tool dependencies
**Likelihood**: Low
**Impact**: Medium
**Mitigation**:
- Check for tool availability early
- Provide clear installation docs
- Graceful degradation (skip if tool missing)

### Risk: Repair loop complexity
**Likelihood**: Medium
**Impact**: Medium
**Mitigation**:
- Start with simple strategies (constraint tightening)
- Add adaptive strategies incrementally
- Extensive testing of repair scenarios

### Risk: Performance targets missed
**Likelihood**: Low
**Impact**: Low
**Mitigation**:
- Profile early in development
- Use caching aggressively
- Parallel validation where safe

### Risk: Integration test failures
**Likelihood**: Medium
**Impact**: Low
**Mitigation**:
- Unit test thoroughly first
- Incremental integration
- Clear error messages for debugging

## Execution Order

**Recommended order for single-threaded execution**:
1. 4.5: RuneExecutor (unblocks 4.3, no dependencies)
2. 4.1: SyntaxValidator (critical path, no dependencies)
3. 4.4: LintValidator (parallel candidate)
4. 4.7: PedanticRavenIntegration (parallel candidate)
5. 4.2: TypeValidator (depends on 4.1)
6. 4.3: TestValidator (depends on 4.5)
7. 4.8: ValidationPipeline (depends on all validators)
8. 4.6: RepairOrchestrator (depends on pipeline)
9. 4.9: Integration tests (depends on all)
10. 4.10: Optimization (final polish)

**Optimized parallel order**:
- **Wave 1**: Start 4.5, 4.1, 4.4, 4.7 (parallel)
- **Wave 2**: Start 4.2 (after 4.1), 4.3 (after 4.5)
- **Wave 3**: Start 4.8 (after all validators)
- **Wave 4**: Start 4.6 (after 4.8)
- **Wave 5**: Run 4.9 (after 4.6)
- **Wave 6**: Run 4.10 (final)

## Success Metrics

**Coverage**:
- Unit tests: 80+ (100 total)
- Integration tests: 25+
- Total tests: 115+
- Test coverage: >85%

**Performance**:
- Syntax: <50ms
- Types: <200ms
- Lint: <100ms
- Pipeline: <500ms (excluding tests)
- Repair: <2s per iteration
- Total: <10s for repair

**Quality**:
- All tests passing
- Type coverage: 100%
- Documentation: Complete
- No lint violations in implementation

**Repair Effectiveness**:
- Success rate: >90% within 3 attempts
- Average attempts: <2
- Constraint learning: patterns stored and reused

## Timeline

**Day 1** (6-8 hours):
- Morning: 4.5 RuneExecutor
- Afternoon: 4.1 SyntaxValidator, 4.4 LintValidator

**Day 2** (6-8 hours):
- Morning: 4.2 TypeValidator, 4.3 TestValidator
- Afternoon: 4.7 PedanticRavenIntegration, 4.8 ValidationPipeline

**Day 3** (4-6 hours):
- Morning: 4.6 RepairOrchestrator
- Afternoon: 4.9 Integration tests, 4.10 Optimization

**Total**: 16-22 hours over 3 days
