# Post-Phase 6 Roadmap - Prioritized Work Plan

**Status**: 📋 Strategic Planning
**Created**: 2025-11-11
**Baseline**: Phase 6 + Path A + B complete (1063 tests, 99.3% passing)

## Prioritization Framework

| Priority | Impact | Effort | ROI | Urgency |
|----------|--------|--------|-----|---------|
| **P0** | High | Low | Very High | Immediate |
| **P1** | High | Medium | High | Soon |
| **P2** | Medium | Low-Medium | Medium | Later |
| **P3** | Low-Medium | High | Low | Optional |

---

## P0: Critical Fixes & Quick Wins (1-2 days)

### Item 1: Complete TODO Items
**Impact**: MEDIUM-HIGH (unlocks features, removes technical debt)
**Effort**: LOW (1 day)
**ROI**: Very High

**Tasks**:
1. JSON Schema → GBNF grammar conversion (`providers/__init__.py:405`)
2. Schema-specific constraints (`llguidance/adapter.py:304`)
3. Pattern mining for Python (`pattern_mining.py:483`)
4. Mnemosyne agent orchestration (`mnemosyne/__init__.py:568`)

**Exit Criteria**:
- All TODO comments resolved
- 15-20 new tests
- No functionality gaps

**Priority**: **P0** - Quick wins, removes blockers

---

### Item 2: Real-World Validation
**Impact**: HIGH (proves system works, finds edge cases)
**Effort**: LOW (1-2 days)
**ROI**: Very High

**Tasks**:
1. Run on 3 real TypeScript projects (small, medium, large)
2. Run on 3 real Python projects
3. HumanEval benchmark (164 Python problems)
4. MBPP benchmark (974 Python problems)
5. Document results and edge cases
6. Fix any critical bugs found

**Exit Criteria**:
- HumanEval pass@1 >50%
- MBPP pass@1 >40%
- Real projects index successfully
- Edge cases documented

**Priority**: **P0** - Validates production readiness

---

## P1: High-Impact Extensions (1-2 weeks)

### Item 3: Rust Language Support
**Impact**: HIGH (3rd most requested language, systems programming)
**Effort**: MEDIUM (3-4 days)
**ROI**: High

**Tasks**:
1. RustIndexer with rust-analyzer integration
2. Rust grammar (lifetimes, traits, generics)
3. 5 Rust examples
4. Documentation
5. ~40 tests

**Exit Criteria**:
- `maze init --language rust` works
- Rust symbols extracted (structs, traits, impl blocks)
- Lifetime annotations parsed
- Examples run successfully

**Priority**: **P1** - Expands to systems programming audience

---

### Item 4: VSCode Extension (Phase 7)
**Impact**: HIGH (best UX, most requested feature)
**Effort**: HIGH (4-5 days)
**ROI**: High

**Tasks**:
1. Extension scaffold
2. Command palette integration
3. Inline code generation
4. Constraint visualization
5. Configuration UI
6. Publishing to marketplace

**Exit Criteria**:
- Published to VSCode marketplace
- "Generate with Maze" context menu works
- Real-time validation feedback
- Downloads >100 in first month

**Priority**: **P1** - High user impact, but higher effort

---

## P2: Performance & Quality (1 week)

### Item 5: Advanced Type Features
**Impact**: MEDIUM (improves generation quality)
**Effort**: MEDIUM (2-3 days)
**ROI**: Medium

**Tasks**:
1. Full type inhabitation search
2. Generic constraint synthesis
3. TypeVar bounds (Python)
4. Protocol support (Python)
5. Mapped/conditional types (TypeScript)

**Exit Criteria**:
- Type search finds complex paths
- Generic types properly constrained
- Type error reduction >95% (from 94%)

**Priority**: **P2** - Quality improvement

---

### Item 6: Performance Optimization
**Impact**: MEDIUM (faster generation)
**Effort**: MEDIUM (2-3 days)
**ROI**: Medium

**Tasks**:
1. Speculative decoding
2. Grammar compilation optimization
3. Parallel validation streams
4. Cache optimization (>80% hit rate target)
5. Profiling and bottleneck removal

**Exit Criteria**:
- Generation <1s (from 2.2s)
- Cache hit rate >80% (from 70%)
- Validation parallelized

**Priority**: **P2** - Nice to have

---

## P3: Additional Languages (2-3 weeks total)

### Item 7: Go Language Support
**Impact**: MEDIUM (popular for backend/cloud)
**Effort**: MEDIUM (3-4 days)
**ROI**: Medium

**Exit Criteria**: Same as Rust

**Priority**: **P3** - Expands language support

---

### Item 8: Zig Language Support
**Impact**: LOW-MEDIUM (growing but niche)
**Effort**: MEDIUM (3-4 days)
**ROI**: Low-Medium

**Exit Criteria**: Same as Rust

**Priority**: **P3** - Completes planned 5 languages

---

## Dependency Graph

```
P0 Items (parallel):
├─ Complete TODOs (1 day) ────┐
└─ Real-World Validation (2d) ─┤
                               ▼
P1 Items:                  Results Review
├─ Rust Support (4d) ──────────┐
└─ VSCode Extension (5d) ──────┤
                               ▼
P2 Items:                  Feature Complete
├─ Advanced Types (3d)
├─ Performance Opt (3d)
└─ Additional Languages (6-8d)
```

---

## Recommended Execution Order

### Week 1: P0 Items
**Days 1-2**: Complete TODO items + Real-world validation
- **Output**: All TODOs resolved, benchmark results

### Week 2-3: P1 Items
**Days 3-6**: Rust language support
**Days 7-11**: VSCode extension

### Week 4+: P2/P3 Items
- Advanced type features
- Performance optimization
- Go and Zig support (if needed)

---

## Resource Allocation

### Immediate (This Week)
- **Focus**: P0 items (TODOs + Validation)
- **Goal**: Production-proven system
- **Deliverable**: Benchmark results, no TODOs

### Near-term (Next 2 Weeks)
- **Focus**: P1 items (Rust + VSCode)
- **Goal**: Multi-language with great UX
- **Deliverable**: 3 languages, IDE integration

### Medium-term (Month 2)
- **Focus**: P2/P3 quality and breadth
- **Goal**: Feature-complete system
- **Deliverable**: 5 languages, optimized

---

## Success Metrics

### P0 Completion
- ✅ Zero TODO comments in codebase
- ✅ HumanEval pass@1 >50%
- ✅ MBPP pass@1 >40%
- ✅ 3 real projects successfully indexed

### P1 Completion
- ✅ Rust fully supported
- ✅ VSCode extension published
- ✅ Downloads >100

### P2 Completion
- ✅ Type error reduction >95%
- ✅ Generation <1s average
- ✅ Cache hit rate >80%

---

## Risk Assessment

**Low Risk** (P0):
- TODOs are small, localized
- Benchmarks use existing infrastructure

**Medium Risk** (P1):
- Rust has complex type system (lifetimes)
- VSCode API may have breaking changes

**High Risk** (P2/P3):
- Performance optimization may require architecture changes
- Additional languages may reveal design issues

---

## Resource Requirements

### External Dependencies
- Rust: `rust-analyzer` (LSP integration)
- VSCode: Node.js, TypeScript, VSCode API
- Benchmarks: HumanEval, MBPP datasets

### Time Estimates
- P0: 2 days
- P1: 9 days
- P2: 6 days
- P3: 6 days
- **Total**: ~4 weeks for all items

---

## Next Steps

1. ✅ Create this roadmap
2. Create detailed specs for P0 items
3. Implement P0 items
4. Review results
5. Plan P1 execution
