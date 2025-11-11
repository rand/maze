# Benchmark Report: Phase 6 Performance Validation

**Timestamp**: 2025-11-11 11:53:09

**Total Benchmarks**: 13

## Overall Statistics

- **Success Rate**: 100.0%
- **Average Duration**: 2946.26ms
- **Median Duration**: 498.49ms
- **P95 Duration**: 0.00ms
- **Average Memory**: 2.79MB


## Indexing Performance

- **Count**: 3
- **Mean Duration**: 70.42ms
- **Min/Max Duration**: 3.44ms / 188.37ms
- **Mean Memory**: 2.62MB


## Generation Performance

- **Count**: 5
- **Mean Duration**: 2240.42ms
- **Min/Max Duration**: 2200.26ms / 2288.10ms
- **Mean Memory**: -0.60MB


## Validation Performance

- **Count**: 3
- **Mean Duration**: 480.91ms
- **Min/Max Duration**: 468.17ms / 498.49ms
- **Mean Memory**: 0.00MB


## Stress Performance

- **Count**: 2
- **Mean Duration**: 12722.64ms
- **Min/Max Duration**: 0.00ms / 25445.28ms
- **Mean Memory**: 15.73MB


## Detailed Results

| Name | Category | Duration (ms) | Memory (MB) | Success |
|------|----------|---------------|-------------|---------|
| Small Project Indexing | indexing | 3.44 | 0.17 | ✅ |
| Medium Project Indexing | indexing | 19.45 | 0.73 | ✅ |
| Large Project Indexing | indexing | 188.37 | 6.95 | ✅ |
| Generation: Create a function that adds two numbers... | generation | 2288.10 | 0.05 | ✅ |
| Generation: Create a TypeScript class with getter an... | generation | 2200.26 | 0.07 | ✅ |
| Generation: Create an async function with error hand... | generation | 2240.95 | -2.57 | ✅ |
| Generation: Create an interface with generic types... | generation | 2214.35 | -0.60 | ✅ |
| Generation: Create a function with complex return ty... | generation | 2258.46 | 0.04 | ✅ |
| Validation: Test 1 | validation | 468.17 | 0.00 | ✅ |
| Validation: Test 2 | validation | 476.08 | 0.00 | ✅ |
| Validation: Test 3 | validation | 498.49 | 0.00 | ✅ |
| Concurrent 10x | stress | 25445.28 | 0.30 | ✅ |
| Memory Profile 30 ops | stress | 0.00 | 31.16 | ✅ |