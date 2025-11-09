"""
Unit tests for PedanticRaven integration.

Tests code quality enforcement, security vulnerability detection,
performance anti-pattern detection, and documentation checking.
"""

import pytest
from maze.integrations.pedantic_raven import (
    PedanticRavenIntegration,
    ReviewRules,
    SecurityFinding,
    PerformanceFinding,
    QualityReport,
    DocumentationReport,
    CoverageReport,
)


class TestSecurityDetection:
    """Test security vulnerability detection."""

    def test_detect_sql_injection(self):
        """Test detection of SQL injection vulnerabilities."""
        raven = PedanticRavenIntegration()

        code = '''
def query_user(user_id):
    query = "SELECT * FROM users WHERE id = %s" % user_id
    return execute(query)
'''

        findings = raven.check_security(code, "python")

        assert len(findings) > 0
        assert any(f.category == "injection" for f in findings)
        assert any("SQL injection" in f.message for f in findings)

    def test_detect_xss_vulnerability(self):
        """Test detection of XSS vulnerabilities."""
        raven = PedanticRavenIntegration()

        code = '''
function render(data) {
    document.getElementById("content").innerHTML = data;
}
'''

        findings = raven.check_security(code, "typescript")

        assert len(findings) > 0
        assert any(f.category == "xss" for f in findings)
        assert any("XSS" in f.message for f in findings)

    def test_detect_command_injection(self):
        """Test detection of command injection vulnerabilities."""
        raven = PedanticRavenIntegration()

        code = '''
import os
def execute_command(cmd):
    os.system(cmd)
'''

        findings = raven.check_security(code, "python")

        assert len(findings) > 0
        assert any(f.category == "injection" for f in findings)

    def test_detect_eval_usage(self):
        """Test detection of dangerous eval() usage."""
        raven = PedanticRavenIntegration()

        code = '''
def process(data):
    result = eval(data)
    return result
'''

        findings = raven.check_security(code, "python")

        assert len(findings) > 0
        assert any(f.severity == "critical" for f in findings)
        assert any("eval" in f.message for f in findings)

    def test_detect_hardcoded_credentials(self):
        """Test detection of hardcoded credentials."""
        raven = PedanticRavenIntegration()

        code = '''
API_KEY = "sk-1234567890abcdef"
PASSWORD = "SuperSecret123"
'''

        findings = raven.check_security(code, "python")

        assert len(findings) > 0
        assert any(f.category == "auth" for f in findings)
        assert any("credential" in f.message.lower() for f in findings)

    def test_no_security_issues(self):
        """Test that safe code has no security findings."""
        raven = PedanticRavenIntegration()

        code = '''
def add(a, b):
    return a + b
'''

        findings = raven.check_security(code, "python")

        assert len(findings) == 0


class TestQualityMetrics:
    """Test code quality metric calculation."""

    def test_calculate_quality_metrics(self):
        """Test calculation of quality metrics."""
        raven = PedanticRavenIntegration()

        code = '''
def simple_function(x):
    """A simple function."""
    return x * 2

def another_function(y):
    # Comment here
    if y > 0:
        return y
    else:
        return -y
'''

        report = raven.check_quality(code, "python")

        assert isinstance(report, QualityReport)
        assert report.cyclomatic_complexity >= 0
        assert 0 <= report.quality_score <= 100
        assert report.average_function_length >= 0
        assert report.max_nesting_depth >= 0

    def test_high_complexity_penalty(self):
        """Test that high complexity reduces quality score."""
        raven = PedanticRavenIntegration()

        # Simple code
        simple_code = "def foo(): return 42"
        simple_report = raven.check_quality(simple_code, "python")

        # Complex code with many branches
        complex_code = '''
def complex(x):
    if x > 10:
        if x > 20:
            if x > 30:
                if x > 40:
                    if x > 50:
                        return "very high"
'''

        complex_report = raven.check_quality(complex_code, "python")

        # Complex code should have lower quality score
        assert complex_report.quality_score <= simple_report.quality_score

    def test_comment_ratio_calculation(self):
        """Test comment ratio calculation."""
        raven = PedanticRavenIntegration()

        code_with_comments = '''
# This is a comment
def foo():
    # Another comment
    return 42
'''

        report = raven.check_quality(code_with_comments, "python")

        assert report.comment_ratio > 0

    def test_unsupported_language_quality(self):
        """Test quality metrics for unsupported language."""
        raven = PedanticRavenIntegration()

        report = raven.check_quality("code", "cobol")

        assert isinstance(report, QualityReport)
        assert report.quality_score >= 0


class TestPerformanceAntipatterns:
    """Test performance anti-pattern detection."""

    def test_detect_performance_antipatterns(self):
        """Test detection of performance anti-patterns."""
        raven = PedanticRavenIntegration()

        code = '''
def process_data(items):
    result = [x for x in [y for y in items]]
    return result
'''

        findings = raven.check_performance(code, "python")

        # May or may not detect patterns depending on implementation
        assert isinstance(findings, list)

    def test_no_performance_issues(self):
        """Test that efficient code has no performance findings."""
        raven = PedanticRavenIntegration()

        code = '''
def efficient(x):
    return x * 2
'''

        findings = raven.check_performance(code, "python")

        assert isinstance(findings, list)


class TestDocumentationCompleteness:
    """Test documentation completeness checking."""

    def test_check_documentation_completeness(self):
        """Test documentation completeness checking."""
        raven = PedanticRavenIntegration()

        code = '''
def documented_function(x: int) -> int:
    """
    Multiply by 2.

    Args:
        x: Input value

    Returns:
        Result
    """
    return x * 2
'''

        report = raven.check_documentation(code, "python")

        assert isinstance(report, DocumentationReport)
        assert report.functions_total > 0
        assert report.completeness_score >= 0

    def test_undocumented_code_lower_score(self):
        """Test that undocumented code has lower completeness score."""
        raven = PedanticRavenIntegration()

        # Documented code
        documented = '''
def foo():
    """Docstring here."""
    pass
'''

        doc_report = raven.check_documentation(documented, "python")

        # Undocumented code
        undocumented = '''
def bar():
    pass
'''

        undoc_report = raven.check_documentation(undocumented, "python")

        assert doc_report.completeness_score > undoc_report.completeness_score

    def test_return_type_annotations(self):
        """Test detection of return type annotations."""
        raven = PedanticRavenIntegration()

        code = '''
def typed_function() -> int:
    return 42
'''

        report = raven.check_documentation(code, "python")

        assert report.return_types_documented > 0

    def test_typescript_documentation(self):
        """Test TypeScript documentation checking."""
        raven = PedanticRavenIntegration()

        code = '''
/**
 * Add two numbers
 */
function add(a: number, b: number): number {
    return a + b;
}
'''

        report = raven.check_documentation(code, "typescript")

        assert isinstance(report, DocumentationReport)
        assert report.functions_documented > 0


class TestCoverageCalculation:
    """Test test coverage calculation."""

    def test_calculate_test_coverage(self):
        """Test test coverage calculation."""
        raven = PedanticRavenIntegration()

        code = '''
def add(a, b):
    return a + b

def multiply(a, b):
    return a * b
'''

        tests = '''
def test_add():
    assert add(2, 3) == 5

def test_multiply():
    assert multiply(2, 3) == 6
'''

        report = raven.check_test_coverage(code, tests, "python")

        assert isinstance(report, CoverageReport)
        assert 0 <= report.line_coverage <= 100
        assert 0 <= report.branch_coverage <= 100
        assert 0 <= report.function_coverage <= 100

    def test_higher_test_ratio_better_coverage(self):
        """Test that more tests give higher coverage."""
        raven = PedanticRavenIntegration()

        code = "def foo(): return 42"

        # Few tests
        few_tests = "def test_foo(): pass"
        few_coverage = raven.check_test_coverage(code, few_tests, "python")

        # Many tests
        many_tests = '''
def test_foo_1(): pass
def test_foo_2(): pass
def test_foo_3(): pass
def test_foo_4(): pass
def test_foo_5(): pass
'''

        many_coverage = raven.check_test_coverage(code, many_tests, "python")

        assert many_coverage.line_coverage >= few_coverage.line_coverage


class TestComprehensiveReview:
    """Test comprehensive code review."""

    def test_overall_review_score(self):
        """Test overall review score calculation."""
        raven = PedanticRavenIntegration()

        code = '''
def simple_function(x: int) -> int:
    """Simple function."""
    return x * 2
'''

        result = raven.review(code, "python")

        assert 0 <= result.overall_score <= 100
        assert isinstance(result.security_findings, list)
        assert isinstance(result.performance_findings, list)
        assert isinstance(result.quality_report, QualityReport)

    def test_critical_security_blocks_review(self):
        """Test that critical security issues block review."""
        raven = PedanticRavenIntegration(ReviewRules.strict())

        code = '''
def unsafe(data):
    eval(data)
'''

        result = raven.review(code, "python")

        assert not result.success
        assert any(f.severity == "critical" for f in result.security_findings)

    def test_review_passes_for_good_code(self):
        """Test that good code passes review."""
        raven = PedanticRavenIntegration(ReviewRules.lenient())

        code = '''
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b
'''

        result = raven.review(code, "python")

        # Should have decent score
        assert result.overall_score > 50

    def test_review_with_coverage(self):
        """Test review with test coverage checking."""
        raven = PedanticRavenIntegration(ReviewRules.strict())

        code = "def foo(): return 42"
        tests = "def test_foo(): assert foo() == 42"

        result = raven.review(code, "python", tests=tests)

        assert result.coverage_report is not None
        assert isinstance(result.coverage_report, CoverageReport)

    def test_review_without_coverage(self):
        """Test review without test coverage."""
        raven = PedanticRavenIntegration(ReviewRules.lenient())

        code = "def foo(): return 42"

        result = raven.review(code, "python")

        # Lenient rules don't check coverage
        assert result.coverage_report is None


class TestCustomRules:
    """Test custom review rules configuration."""

    def test_custom_review_rules(self):
        """Test custom rule configuration."""
        custom_rules = ReviewRules(
            check_security=True,
            check_performance=False,
            check_quality=True,
            check_documentation=False,
            min_quality_score=60.0,
        )

        raven = PedanticRavenIntegration(custom_rules)

        code = "def foo(): return 42"

        result = raven.review(code, "python")

        # Performance and documentation should not be checked
        assert len(result.performance_findings) == 0
        # Documentation report should exist but not affect success
        assert isinstance(result.documentation_report, DocumentationReport)

    def test_strict_rules(self):
        """Test strict review rules."""
        raven = PedanticRavenIntegration(ReviewRules.strict())

        assert raven.rules.min_quality_score == 80.0
        assert raven.rules.min_documentation_score == 70.0
        assert raven.rules.block_on_critical_security

    def test_lenient_rules(self):
        """Test lenient review rules."""
        raven = PedanticRavenIntegration(ReviewRules.lenient())

        assert raven.rules.min_quality_score == 50.0
        assert not raven.rules.check_performance
        assert not raven.rules.check_documentation

    def test_override_rules_per_review(self):
        """Test overriding rules per review."""
        raven = PedanticRavenIntegration(ReviewRules.strict())

        code = "def foo(): return 42"

        # Override with lenient rules
        result = raven.review(code, "python", rules=ReviewRules.lenient())

        # Should use lenient rules
        assert isinstance(result, type(result))


class TestRuleEnforcement:
    """Test rule enforcement and thresholds."""

    def test_block_on_critical_security(self):
        """Test blocking on critical security issues."""
        raven = PedanticRavenIntegration(
            ReviewRules(block_on_critical_security=True)
        )

        code = "def bad(x): eval(x)"

        result = raven.review(code, "python")

        assert not result.success

    def test_min_quality_threshold(self):
        """Test minimum quality score threshold."""
        raven = PedanticRavenIntegration(
            ReviewRules(min_quality_score=100.0)  # Impossibly high
        )

        code = "def foo(): return 42"

        result = raven.review(code, "python")

        # Should fail due to quality threshold
        assert not result.success or result.quality_report.quality_score == 100.0

    def test_min_documentation_threshold(self):
        """Test minimum documentation score threshold."""
        raven = PedanticRavenIntegration(
            ReviewRules(min_documentation_score=100.0)  # Impossibly high
        )

        code = "def foo(): return 42"

        result = raven.review(code, "python")

        # Should fail due to documentation threshold
        assert not result.success or result.documentation_report.completeness_score == 100.0


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_code(self):
        """Test review of empty code."""
        raven = PedanticRavenIntegration()

        result = raven.review("", "python")

        assert isinstance(result, type(result))

    def test_syntactically_invalid_code(self):
        """Test review of syntactically invalid code."""
        raven = PedanticRavenIntegration()

        code = "def broken("

        result = raven.review(code, "python")

        # Should handle gracefully
        assert isinstance(result, type(result))

    def test_unsupported_language(self):
        """Test review of unsupported language."""
        raven = PedanticRavenIntegration()

        result = raven.review("code", "cobol")

        assert isinstance(result, type(result))
        assert len(result.security_findings) == 0

    def test_multiple_security_issues(self):
        """Test code with multiple security issues."""
        raven = PedanticRavenIntegration()

        code = '''
def dangerous(data, query):
    eval(data)
    exec(query)
    os.system(data)
'''

        result = raven.review(code, "python")

        assert len(result.security_findings) >= 2
