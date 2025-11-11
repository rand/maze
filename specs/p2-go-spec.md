# P2: Go Language Support - Specification

**Priority**: P2 (High Value)
**Effort**: 3 days
**Impact**: MEDIUM-HIGH (backend/cloud programming, 4th language)
**Pattern**: Follow TypeScript/Python/Rust success

## Executive Summary

Add Go language support following the proven 3-language pattern. Go is essential for backend services, cloud infrastructure, and microservices - completing coverage of major programming domains.

## Objectives

### 1. Go Indexer
**Goal**: Extract symbols, types, and patterns from Go codebases

**Go-Specific Features**:
- Interfaces (implicit implementation)
- Goroutines and channels
- Defer statements
- Methods on types
- Package system
- Error handling (error return values)

**Symbols to Extract**:
```go
// Functions
func Process(data string) (string, error)
func New() *Service

// Methods
func (s *Service) Start() error

// Interfaces
type Repository interface {
    Find(id string) (*User, error)
    Save(user *User) error
}

// Structs
type User struct {
    ID    string `json:"id"`
    Name  string `json:"name"`
}

// Type aliases
type UserID string
```

### 2. Go Grammar (Already Exists)
**Status**: Verify `src/maze/synthesis/grammars/` has Go templates

### 3. Go Examples (5)
1. Function with error return
2. Struct with JSON tags and methods
3. Interface and implementation
4. Goroutine with channels
5. Test generation (testing package)

## Success Criteria

1. ✅ `maze init --language go` works
2. ✅ GoIndexer extracts functions, structs, interfaces, methods
3. ✅ Grammar handles Go syntax
4. ✅ All 5 examples run
5. ✅ Performance: >1000 symbols/sec
6. ✅ 25+ tests passing

## Estimated Effort

- Day 1: GoIndexer (6h, 16 tests)
- Day 2: Grammar integration (2h, 5 tests)
- Day 3: Examples + docs (4h, 6 tests)
- **Total**: 12 hours (2-3 days)

## Risk: LOW
Following proven pattern 3 times, Go is simpler than Rust (no lifetimes).
