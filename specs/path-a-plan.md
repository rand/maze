# Path A: Provider Integration & Grammar Loading - Execution Plan

**Status**: 📋 Ready for Implementation (Phase 3: Full Spec → Plan)
**Timeline**: 1-2 days
**Critical Path**: Grammar Loading → Provider Integration → Pipeline Integration → Testing

## Task Ordering & Dependencies

### Task 1: Grammar Template Loading (maze-pa.1)
**Duration**: 2-3 hours
**Priority**: HIGH (blocks provider integration)

**Subtasks**:
1. Read existing TypeScript grammar template
2. Update `Pipeline._synthesize_constraints()` to load grammar
3. Integrate with GrammarBuilder
4. Add grammar caching
5. Unit tests (5 tests)

**Dependencies**: None
**Output**: Grammar properly loaded and cached

**Exit Criteria**:
- Grammar template loads successfully
- Grammar cached for reuse
- Tests validate grammar structure
- Performance: <50ms load, <1ms from cache

---

### Task 2: Provider Adapter Integration (maze-pa.2)
**Duration**: 3-4 hours
**Priority**: HIGH (critical path)

**Subtasks**:
1. Import provider adapters in pipeline
2. Create provider factory/router
3. Implement `_generate_with_constraints()` properly
4. Pass grammar to provider
5. Handle API responses
6. Error handling and retries
7. Unit tests (10 tests)

**Dependencies**: Grammar loading (maze-pa.1)
**Output**: Real LLM generation working

**Exit Criteria**:
- Provider selected based on config
- Grammar passed to provider
- Real code generated
- Errors handled gracefully
- Tests with mocked provider

---

### Task 3: Grammar Flow Through Repair (maze-pa.3)
**Duration**: 1-2 hours
**Priority**: MEDIUM

**Subtasks**:
1. Store grammar from generation step
2. Pass grammar to repair orchestrator
3. Update repair to use grammar for refinement
4. Unit tests (3 tests)

**Dependencies**: Provider integration (maze-pa.2)
**Output**: Repair receives and uses grammar

**Exit Criteria**:
- Grammar stored in PipelineResult
- Repair receives grammar
- Constraint refinement works
- Tests validate flow

---

### Task 4: Provider Configuration (maze-pa.4)
**Duration**: 2 hours
**Priority**: MEDIUM

**Subtasks**:
1. API key handling from environment
2. Provider-specific config (timeout, retries)
3. Provider availability checking
4. Graceful fallback
5. Tests (5 tests)

**Dependencies**: Provider integration (maze-pa.2)
**Output**: Robust provider configuration

**Exit Criteria**:
- API keys loaded securely
- Timeouts enforced
- Retries work
- Missing API key handled gracefully

---

### Task 5: End-to-End Integration Testing (maze-pa.5)
**Duration**: 2-3 hours
**Priority**: HIGH

**Subtasks**:
1. E2E test with real generation flow
2. Test grammar application
3. Test validation on real generated code
4. Test repair with actual errors
5. Integration tests (10 tests)

**Dependencies**: All above tasks
**Output**: Complete working pipeline

**Exit Criteria**:
- Full flow works: init → index → generate → validate
- Real TypeScript code generated
- Validation catches real errors
- Repair fixes real issues
- Performance targets met

---

### Task 6: Documentation Updates (maze-pa.6)
**Duration**: 1 hour
**Priority**: LOW

**Subtasks**:
1. Update examples to show real generation
2. Update getting-started.md
3. Add provider setup guide
4. Update CLAUDE.md status

**Dependencies**: E2E tests passing (maze-pa.5)
**Output**: Updated documentation

---

## Critical Path

```
Grammar Loading (2-3h)
    ↓
Provider Integration (3-4h)
    ↓
Repair Flow (1-2h)
    ↓
E2E Testing (2-3h)
    ↓
Documentation (1h)
```

**Total Critical Path**: 9-13 hours (~1-2 days)

## Parallel Work Streams

Stream A (Critical): Grammar + Provider + Repair
Stream B (Parallel): Configuration + Testing

Can parallelize:
- Provider config (Task 4) while doing E2E tests (Task 5)

## Test Plan

**New Tests**: ~33
- Grammar loading: 5 tests
- Provider integration: 10 tests
- Grammar repair flow: 3 tests
- Provider configuration: 5 tests
- E2E integration: 10 tests

**Total After Path A**: 1007 + 33 = **1040 tests**

## Performance Validation

Must maintain targets:
- Pipeline total: <10s ✅
- Grammar load: <50ms (first), <1ms (cached)
- Provider call: <8s (depends on LLM)

## Risk Mitigation

**Risk**: API keys not available for testing
**Mitigation**: Mock provider responses, test with real API in CI only

**Risk**: Grammar compilation errors
**Mitigation**: Validate grammars in unit tests before integration

**Risk**: Provider API changes
**Mitigation**: Use latest stable client libraries, pin versions
