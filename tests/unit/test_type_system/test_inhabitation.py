"""
Tests for type inhabitation solver.
"""

import pytest
from maze.type_system.inhabitation import (
    InhabitationSolver,
    Operation,
    InhabitationPath,
)
from maze.core.types import (
    Type, TypeContext, FunctionSignature, TypeParameter, ClassType
)


class TestInhabitationSolver:
    """Test type inhabitation solver."""

    def test_direct_path_variable_exists(self):
        """Test finding direct path when variable has target type."""
        solver = InhabitationSolver()

        context = TypeContext(variables={"x": Type("number")})

        paths = solver.find_paths(Type("unknown"), Type("number"), context)

        assert len(paths) >= 1
        assert paths[0].target == Type("number")
        assert paths[0].cost == 0.0  # Direct variable access is free

    def test_function_application_path(self):
        """Test finding path through function application."""
        solver = InhabitationSolver()

        # Function: toString: number -> string
        to_string = FunctionSignature(
            name="toString",
            parameters=[TypeParameter("n", Type("number"))],
            return_type=Type("string")
        )

        context = TypeContext(
            variables={"x": Type("number")},
            functions={"toString": to_string}
        )

        # Find path from number to string
        paths = solver.find_paths(Type("number"), Type("string"), context)

        assert len(paths) >= 1
        # Should find path via toString
        assert any("toString" in str(p) for p in paths)

    def test_property_access_path(self):
        """Test finding path through property access."""
        solver = InhabitationSolver()

        # Class Person with name property
        person_class = ClassType(
            name="Person",
            properties={"name": Type("string"), "age": Type("number")},
            methods={}
        )

        context = TypeContext(
            classes={"Person": person_class}
        )

        # Find path from Person to string via name property
        paths = solver.find_paths(Type("Person"), Type("string"), context)

        assert len(paths) >= 1
        # Should find path via property access
        assert any("name" in str(p) for p in paths)

    def test_multi_step_path(self):
        """Test finding multi-step transformation path."""
        solver = InhabitationSolver()

        # Person has address: Address, Address has street: string
        address_class = ClassType(
            name="Address",
            properties={"street": Type("string"), "city": Type("string")},
            methods={}
        )

        person_class = ClassType(
            name="Person",
            properties={"name": Type("string"), "address": Type("Address")},
            methods={}
        )

        context = TypeContext(
            classes={"Person": person_class, "Address": address_class}
        )

        # Find path from Person to string via address.street
        paths = solver.find_paths(Type("Person"), Type("string"), context)

        assert len(paths) >= 1
        # Should find multi-step paths
        multi_step = [p for p in paths if len(p.operations) > 1]
        assert len(multi_step) >= 1

    def test_no_path_exists(self):
        """Test when no path exists to target type."""
        solver = InhabitationSolver()

        context = TypeContext(variables={"x": Type("number")})

        # Try to find path to a type not in context
        paths = solver.find_paths(Type("number"), Type("CustomType"), context)

        # Should return empty list
        assert len(paths) == 0

    def test_path_cost_calculation(self):
        """Test that path costs are calculated correctly."""
        solver = InhabitationSolver()

        to_string = FunctionSignature(
            name="toString",
            parameters=[TypeParameter("n", Type("number"))],
            return_type=Type("string")
        )

        context = TypeContext(
            variables={"x": Type("number")},
            functions={"toString": to_string}
        )

        paths = solver.find_paths(Type("number"), Type("string"), context)

        assert len(paths) >= 1
        # Function application should have cost 1.0
        func_path = next(p for p in paths if "toString" in str(p))
        assert func_path.cost == 1.0

    def test_path_ranking(self):
        """Test that paths are ranked by cost."""
        solver = InhabitationSolver()

        person_class = ClassType(
            name="Person",
            properties={"name": Type("string")},
            methods={}
        )

        to_string = FunctionSignature(
            name="toString",
            parameters=[TypeParameter("p", Type("Person"))],
            return_type=Type("string")
        )

        context = TypeContext(
            variables={"person": Type("Person")},
            classes={"Person": person_class},
            functions={"toString": to_string}
        )

        # Find paths from Person to string
        paths = solver.find_paths(Type("Person"), Type("string"), context)

        # Should have at least 2 paths
        assert len(paths) >= 2

        # Paths should be sorted by cost
        for i in range(len(paths) - 1):
            assert paths[i].cost <= paths[i + 1].cost

    def test_pruning_deep_paths(self):
        """Test that search is pruned at max depth."""
        solver = InhabitationSolver(max_depth=2)

        # Create deep nesting
        address_class = ClassType(
            name="Address",
            properties={"street": Type("string")},
            methods={}
        )

        person_class = ClassType(
            name="Person",
            properties={"address": Type("Address")},
            methods={}
        )

        company_class = ClassType(
            name="Company",
            properties={"ceo": Type("Person")},
            methods={}
        )

        context = TypeContext(
            classes={
                "Company": company_class,
                "Person": person_class,
                "Address": address_class
            }
        )

        # This would require 3 steps: Company -> Person -> Address -> string
        # With max_depth=2, should not find full path
        paths = solver.find_paths(Type("Company"), Type("string"), context)

        # Should find shorter paths only
        assert all(len(p.operations) <= 2 for p in paths)

    def test_caching_paths(self):
        """Test that paths are cached."""
        solver = InhabitationSolver()

        context = TypeContext(variables={"x": Type("number")})

        # First call
        paths1 = solver.find_paths(Type("unknown"), Type("number"), context)

        # Check cache stats
        stats_before = solver.get_cache_stats()
        assert stats_before["misses"] == 1
        assert stats_before["hits"] == 0

        # Second call (should use cache)
        paths2 = solver.find_paths(Type("unknown"), Type("number"), context)

        # Should be same paths
        assert len(paths1) == len(paths2)

        # Cache should have hit
        stats_after = solver.get_cache_stats()
        assert stats_after["hits"] == 1
        assert stats_after["hit_rate"] > 0.0

    def test_cycle_detection(self):
        """Test that cycles are detected and avoided."""
        solver = InhabitationSolver()

        # Create self-referential class
        node_class = ClassType(
            name="Node",
            properties={"next": Type("Node"), "value": Type("number")},
            methods={}
        )

        context = TypeContext(
            classes={"Node": node_class}
        )

        # Search should not infinite loop
        paths = solver.find_paths(Type("Node"), Type("number"), context)

        # Should find path via value property
        assert len(paths) >= 1
        assert any("value" in str(p) for p in paths)

    def test_max_depth_limit(self):
        """Test that max depth limit is enforced."""
        solver = InhabitationSolver(max_depth=1)

        person_class = ClassType(
            name="Person",
            properties={"address": Type("Address")},
            methods={}
        )

        address_class = ClassType(
            name="Address",
            properties={"street": Type("string")},
            methods={}
        )

        context = TypeContext(
            classes={"Person": person_class, "Address": address_class}
        )

        # 2-step path: Person -> Address -> string
        paths = solver.find_paths(Type("Person"), Type("string"), context)

        # With max_depth=1, should not find 2-step path
        assert all(len(p.operations) <= 1 for p in paths)

    def test_path_to_code_conversion(self):
        """Test converting path to code."""
        # Direct variable use
        use_op = Operation("use x", Type("unknown"), Type("number"))
        path1 = InhabitationPath([use_op], Type("unknown"), Type("number"))
        code1 = path1.to_code("source")
        assert code1 == "x"

        # Function call
        call_op = Operation("call toString", Type("number"), Type("string"))
        path2 = InhabitationPath([call_op], Type("number"), Type("string"))
        code2 = path2.to_code("x")
        assert code2 == "toString(x)"

        # Property access
        prop_op = Operation("access name", Type("Person"), Type("string"))
        path3 = InhabitationPath([prop_op], Type("Person"), Type("string"))
        code3 = path3.to_code("person")
        assert code3 == "person.name"

    def test_is_inhabitable_true(self):
        """Test is_inhabitable returns True when type can be inhabited."""
        solver = InhabitationSolver()

        context = TypeContext(variables={"x": Type("number")})

        assert solver.is_inhabitable(Type("number"), context) is True

    def test_is_inhabitable_false(self):
        """Test is_inhabitable returns False when type cannot be inhabited."""
        solver = InhabitationSolver()

        context = TypeContext(variables={"x": Type("number")})

        # CustomType is not available
        assert solver.is_inhabitable(Type("CustomType"), context) is False

    def test_find_best_path(self):
        """Test finding lowest-cost path."""
        solver = InhabitationSolver()

        person_class = ClassType(
            name="Person",
            properties={"name": Type("string")},
            methods={}
        )

        to_string = FunctionSignature(
            name="toString",
            parameters=[TypeParameter("p", Type("Person"))],
            return_type=Type("string")
        )

        context = TypeContext(
            classes={"Person": person_class},
            functions={"toString": to_string}
        )

        # Find best path
        best = solver.find_best_path(Type("Person"), Type("string"), context)

        assert best is not None
        # Property access (cost 0.5) should be cheaper than function call (cost 1.0)
        assert "name" in str(best)
        assert best.cost == 0.5

    def test_cache_clear(self):
        """Test clearing the cache."""
        solver = InhabitationSolver()

        context = TypeContext(variables={"x": Type("number")})

        # Populate cache
        solver.find_paths(Type("unknown"), Type("number"), context)

        stats_before = solver.get_cache_stats()
        assert stats_before["size"] > 0

        # Clear cache
        solver.clear_cache()

        stats_after = solver.get_cache_stats()
        assert stats_after["size"] == 0
        assert stats_after["hits"] == 0
        assert stats_after["misses"] == 0


class TestOperation:
    """Test Operation dataclass."""

    def test_operation_creation(self):
        """Test creating an operation."""
        op = Operation(
            name="toString",
            input_type=Type("number"),
            output_type=Type("string"),
            cost=1.0
        )

        assert op.name == "toString"
        assert op.input_type == Type("number")
        assert op.output_type == Type("string")
        assert op.cost == 1.0

    def test_operation_applicable(self):
        """Test checking if operation is applicable."""
        op = Operation(
            name="toString",
            input_type=Type("number"),
            output_type=Type("string")
        )

        assert op.applicable(Type("number")) is True
        assert op.applicable(Type("string")) is False

    def test_operation_apply(self):
        """Test applying an operation."""
        op = Operation(
            name="toString",
            input_type=Type("number"),
            output_type=Type("string")
        )

        result = op.apply(Type("number"))
        assert result == Type("string")


class TestInhabitationPath:
    """Test InhabitationPath dataclass."""

    def test_path_creation(self):
        """Test creating a path."""
        op = Operation("toString", Type("number"), Type("string"))
        path = InhabitationPath([op], Type("number"), Type("string"))

        assert len(path.operations) == 1
        assert path.source == Type("number")
        assert path.target == Type("string")

    def test_path_cost(self):
        """Test calculating path cost."""
        op1 = Operation("step1", Type("A"), Type("B"), cost=1.0)
        op2 = Operation("step2", Type("B"), Type("C"), cost=2.0)

        path = InhabitationPath([op1, op2], Type("A"), Type("C"))

        assert path.cost == 3.0

    def test_empty_path_cost(self):
        """Test empty path has zero cost."""
        path = InhabitationPath([], Type("number"), Type("number"))
        assert path.cost == 0.0
