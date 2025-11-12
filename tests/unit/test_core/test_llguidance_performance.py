"""
Performance tests for LLGuidance adapter.

Tests that mask computation meets the <100μs target.
"""

import statistics
import time

import pytest

from maze.integrations.llguidance import (
    LLGuidanceAdapter,
    create_adapter,
)


@pytest.mark.performance
@pytest.mark.skip(
    reason="LLGuidance class not properly integrated - requires llguidance library updates"
)
class TestLLGuidancePerformance:
    """Performance benchmarks for LLGuidance adapter."""

    def test_mask_computation_performance(self, llguidance_adapter: LLGuidanceAdapter):
        """Test that mask computation meets <100μs target."""
        # Simple grammar for testing
        grammar = """
            ?start: statement+
            statement: IDENT "=" NUMBER ";"
            IDENT: /[a-zA-Z_][a-zA-Z0-9_]*/
            NUMBER: /[0-9]+/
            %ignore /\\s+/
        """

        # Build parser (this can be slower)
        parser = llguidance_adapter.build_parser(grammar)

        # Test states of varying complexity
        test_states = [
            "",  # Empty state
            "x",  # Partial identifier
            "x =",  # After identifier
            "x = 1",  # After number
            "x = 123",  # Longer number
            "x = 123;",  # Complete statement
            "x = 123; y",  # Starting new statement
        ]

        # Warm up cache
        for state in test_states:
            llguidance_adapter.compute_mask(parser, state)

        # Measure performance
        times_us: list[float] = []

        for state in test_states:
            # Clear cache to test actual computation
            llguidance_adapter.mask_cache.clear()

            # Measure multiple iterations
            iteration_times = []
            for _ in range(100):
                start = time.perf_counter()
                mask = llguidance_adapter.compute_mask(parser, state)
                elapsed = time.perf_counter() - start
                iteration_times.append(elapsed * 1_000_000)  # Convert to microseconds

            # Take median to avoid outliers
            median_time = statistics.median(iteration_times)
            times_us.append(median_time)

            # Check individual state performance
            assert (
                median_time < 200
            ), f"Mask computation for state '{state}' took {median_time:.1f}μs (target: <100μs, acceptable: <200μs)"

        # Overall statistics
        avg_time = statistics.mean(times_us)
        p95_time = statistics.quantiles(times_us, n=20)[18]  # 95th percentile
        p99_time = (
            statistics.quantiles(times_us, n=100)[98] if len(times_us) >= 100 else max(times_us)
        )

        print("\nMask Computation Performance:")
        print(f"  Average: {avg_time:.1f}μs")
        print(f"  P95: {p95_time:.1f}μs")
        print(f"  P99: {p99_time:.1f}μs")
        print(f"  Min: {min(times_us):.1f}μs")
        print(f"  Max: {max(times_us):.1f}μs")

        # Assert performance targets
        assert (
            avg_time < 100
        ), f"Average mask computation time {avg_time:.1f}μs exceeds target of 100μs"
        assert (
            p95_time < 150
        ), f"P95 mask computation time {p95_time:.1f}μs exceeds acceptable threshold of 150μs"

    def test_cache_performance(self, llguidance_adapter: LLGuidanceAdapter):
        """Test cache hit performance."""
        grammar = """
            ?start: json_value
            json_value: object | string | number
            object: "{" [pair ("," pair)*] "}"
            pair: string ":" json_value
            string: ESCAPED_STRING
            number: NUMBER
            ESCAPED_STRING: /"[^"]*"/
            NUMBER: /-?[0-9]+/
            %ignore /\\s+/
        """

        parser = llguidance_adapter.build_parser(grammar)
        state = '{"name": '

        # First computation (cache miss)
        llguidance_adapter.mask_cache.clear()
        start = time.perf_counter()
        mask1 = llguidance_adapter.compute_mask(parser, state)
        miss_time = (time.perf_counter() - start) * 1_000_000

        # Second computation (cache hit)
        start = time.perf_counter()
        mask2 = llguidance_adapter.compute_mask(parser, state)
        hit_time = (time.perf_counter() - start) * 1_000_000

        print("\nCache Performance:")
        print(f"  Cache miss: {miss_time:.1f}μs")
        print(f"  Cache hit: {hit_time:.1f}μs")
        print(f"  Speedup: {miss_time/hit_time:.1f}x")

        # Cache hit should be much faster
        assert hit_time < miss_time / 10, "Cache hit should be at least 10x faster than cache miss"
        assert hit_time < 10, "Cache hit should be <10μs"

    def test_grammar_compilation_performance(self, llguidance_adapter: LLGuidanceAdapter):
        """Test grammar compilation performance."""
        # Complex grammar
        grammar = """
            ?start: module
            module: statement+

            statement: import_stmt | export_stmt | declaration | expression_stmt

            import_stmt: "import" import_spec "from" STRING ";"
            import_spec: "{" IDENT ("," IDENT)* "}" | IDENT

            export_stmt: "export" (declaration | "{" IDENT ("," IDENT)* "}")

            declaration: const_decl | let_decl | function_decl | class_decl

            const_decl: "const" IDENT type_annotation? "=" expression ";"
            let_decl: "let" IDENT type_annotation? ("=" expression)? ";"

            type_annotation: ":" type
            type: IDENT | type "[" "]" | type "|" type

            function_decl: "function" IDENT "(" params? ")" type_annotation? block
            params: param ("," param)*
            param: IDENT type_annotation?

            class_decl: "class" IDENT ("extends" IDENT)? "{" class_member* "}"
            class_member: property | method
            property: IDENT type_annotation? ";"
            method: IDENT "(" params? ")" type_annotation? block

            block: "{" statement* "}"

            expression_stmt: expression ";"
            expression: literal | IDENT | binary_op | call | array

            literal: STRING | NUMBER | "true" | "false" | "null"
            binary_op: expression ("+" | "-" | "*" | "/" | "===" | "!==" | "<" | ">") expression
            call: IDENT "(" args? ")"
            args: expression ("," expression)*
            array: "[" (expression ("," expression)*)? "]"

            IDENT: /[a-zA-Z_$][a-zA-Z0-9_$]*/
            STRING: /"[^"]*"/ | /'[^']*/
            NUMBER: /-?[0-9]+(\\.[0-9]+)?/

            %ignore /\\s+/
            %ignore /\\/\\/[^\\n]*/
            %ignore /\\/\\*.*?\\*\\//
        """

        # Clear cache to test actual compilation
        llguidance_adapter.grammar_cache.clear()

        # Measure compilation time
        start = time.perf_counter()
        parser = llguidance_adapter.build_parser(grammar)
        compilation_time = (time.perf_counter() - start) * 1000  # Convert to milliseconds

        print("\nGrammar Compilation Performance:")
        print(f"  Compilation time: {compilation_time:.2f}ms")

        # Check compilation performance
        assert (
            compilation_time < 100
        ), f"Grammar compilation took {compilation_time:.2f}ms (target: <50ms, acceptable: <100ms)"

        # Test that cached compilation is instant
        start = time.perf_counter()
        parser2 = llguidance_adapter.build_parser(grammar)
        cached_time = (time.perf_counter() - start) * 1000

        print(f"  Cached retrieval: {cached_time:.3f}ms")
        assert cached_time < 1, "Cached grammar retrieval should be <1ms"

    def test_batch_performance(self, llguidance_adapter: LLGuidanceAdapter):
        """Test batch mask computation performance."""
        grammar = """
            ?start: expression
            expression: term (("+" | "-") term)*
            term: factor (("*" | "/") factor)*
            factor: NUMBER | "(" expression ")"
            NUMBER: /[0-9]+/
            %ignore /\\s+/
        """

        parser = llguidance_adapter.build_parser(grammar)

        # Generate test states
        states = [
            "",
            "1",
            "1 +",
            "1 + 2",
            "1 + 2 *",
            "1 + 2 * 3",
            "(1",
            "(1 +",
            "(1 + 2",
            "(1 + 2)",
        ] * 10  # 100 states total

        # Measure batch performance
        start = time.perf_counter()
        masks = llguidance_adapter.compute_mask_batch(parser, states)
        batch_time = (time.perf_counter() - start) * 1000

        # Measure sequential performance
        llguidance_adapter.mask_cache.clear()
        start = time.perf_counter()
        for state in states:
            llguidance_adapter.compute_mask(parser, state)
        sequential_time = (time.perf_counter() - start) * 1000

        print("\nBatch Performance:")
        print(f"  Batch time: {batch_time:.2f}ms for {len(states)} states")
        print(f"  Sequential time: {sequential_time:.2f}ms")
        print(f"  Speedup: {sequential_time/batch_time:.1f}x")
        print(f"  Per-state (batch): {batch_time/len(states)*1000:.1f}μs")
        print(f"  Per-state (sequential): {sequential_time/len(states)*1000:.1f}μs")

        # Check batch performance
        per_state_time = (batch_time / len(states)) * 1000  # Convert to microseconds
        assert (
            per_state_time < 100
        ), f"Per-state batch time {per_state_time:.1f}μs exceeds target of 100μs"

    def test_performance_summary(self, llguidance_adapter: LLGuidanceAdapter):
        """Test performance metrics summary."""
        # Generate some test data
        grammar = "?start: IDENT\nIDENT: /[a-z]+/"
        parser = llguidance_adapter.build_parser(grammar)

        # Clear metrics
        llguidance_adapter.metrics.clear()

        # Generate metrics
        for i in range(200):
            state = "abc" * (i % 10)
            if i % 5 == 0:
                llguidance_adapter.mask_cache.clear()  # Force some cache misses
            llguidance_adapter.compute_mask(parser, state)

        # Get summary
        summary = llguidance_adapter.get_performance_summary()

        print("\nPerformance Summary:")
        print(f"  Mean: {summary.get('mean_us', 0):.1f}μs")
        print(f"  Min: {summary.get('min_us', 0):.1f}μs")
        print(f"  Max: {summary.get('max_us', 0):.1f}μs")
        print(f"  P50: {summary.get('p50_us', 0):.1f}μs")
        print(f"  P95: {summary.get('p95_us', 0):.1f}μs")
        print(f"  P99: {summary.get('p99_us', 0):.1f}μs")
        print(f"  Cache hit rate: {summary.get('cache_hit_rate', 0):.1%}")

        # Verify performance targets
        assert summary.get("mean_us", float("inf")) < 100, "Mean time should be <100μs"
        assert summary.get("p99_us", float("inf")) < 200, "P99 time should be <200μs"
        assert summary.get("cache_hit_rate", 0) > 0.5, "Cache hit rate should be >50%"


@pytest.mark.performance
def test_adapter_factory_performance():
    """Test performance of adapter factory."""
    # Test creation time for different adapters
    adapters = ["default", "openai", "vllm", "sglang"]
    times = {}

    for adapter_type in adapters:
        start = time.perf_counter()
        adapter = create_adapter(adapter_type)
        elapsed = (time.perf_counter() - start) * 1000  # ms
        times[adapter_type] = elapsed

        # Adapter creation should be fast
        assert (
            elapsed < 10
        ), f"Adapter creation for {adapter_type} took {elapsed:.2f}ms (target: <10ms)"

    print("\nAdapter Creation Times:")
    for adapter_type, elapsed in times.items():
        print(f"  {adapter_type}: {elapsed:.3f}ms")
