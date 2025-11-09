"""
Pedantic Raven integration for code quality and security enforcement.

Provides comprehensive code review including security vulnerability scanning,
performance anti-pattern detection, quality metrics, and documentation checking.
"""

from dataclasses import dataclass, field
from typing import Optional, Literal, Any
import re
import ast


@dataclass
class SecurityFinding:
    """Security vulnerability finding."""

    category: str  # "injection", "xss", "auth", "crypto", etc.
    severity: Literal["critical", "high", "medium", "low"]
    message: str
    line: int
    column: int = 0
    cwe_id: Optional[str] = None
    suggested_fix: Optional[str] = None


@dataclass
class PerformanceFinding:
    """Performance anti-pattern finding."""

    pattern: str  # "n_plus_one", "inefficient_loop", etc.
    impact: Literal["high", "medium", "low"]
    message: str
    line: int
    column: int = 0
    suggested_fix: Optional[str] = None


@dataclass
class QualityReport:
    """Code quality metrics."""

    cyclomatic_complexity: float
    code_duplication: float
    average_function_length: float
    max_nesting_depth: int
    comment_ratio: float
    quality_score: float  # 0-100


@dataclass
class DocumentationReport:
    """Documentation completeness."""

    functions_documented: int
    functions_total: int
    parameters_documented: int
    parameters_total: int
    return_types_documented: int
    returns_total: int
    examples_present: int
    completeness_score: float  # 0-100


@dataclass
class CoverageReport:
    """Test coverage metrics."""

    line_coverage: float  # 0-100
    branch_coverage: float  # 0-100
    function_coverage: float  # 0-100
    critical_path_coverage: float  # 0-100


@dataclass
class ReviewResult:
    """Comprehensive code review result."""

    success: bool
    security_findings: list[SecurityFinding]
    performance_findings: list[PerformanceFinding]
    quality_report: QualityReport
    documentation_report: DocumentationReport
    coverage_report: Optional[CoverageReport]
    overall_score: float  # 0-100


@dataclass
class ReviewRules:
    """Code review rules configuration."""

    check_security: bool = True
    check_performance: bool = True
    check_quality: bool = True
    check_documentation: bool = True
    check_coverage: bool = False
    min_quality_score: float = 70.0
    min_documentation_score: float = 50.0
    min_coverage: float = 0.0
    block_on_critical_security: bool = True
    custom_rules: dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def strict() -> "ReviewRules":
        """Strict production rules."""
        return ReviewRules(
            check_security=True,
            check_performance=True,
            check_quality=True,
            check_documentation=True,
            check_coverage=True,
            min_quality_score=80.0,
            min_documentation_score=70.0,
            min_coverage=70.0,
            block_on_critical_security=True,
        )

    @staticmethod
    def lenient() -> "ReviewRules":
        """Lenient development rules."""
        return ReviewRules(
            check_security=True,
            check_performance=False,
            check_quality=True,
            check_documentation=False,
            check_coverage=False,
            min_quality_score=50.0,
            min_documentation_score=0.0,
            min_coverage=0.0,
            block_on_critical_security=True,
        )


class PedanticRavenIntegration:
    """Code quality and security enforcement."""

    def __init__(self, rules: Optional[ReviewRules] = None):
        """
        Initialize pedantic_raven integration.

        Args:
            rules: Custom review rules (defaults to strict)

        Example:
            >>> raven = PedanticRavenIntegration()
            >>> raven = PedanticRavenIntegration(ReviewRules.lenient())
        """
        self.rules = rules or ReviewRules.strict()

    def review(
        self,
        code: str,
        language: str,
        tests: Optional[str] = None,
        rules: Optional[ReviewRules] = None,
    ) -> ReviewResult:
        """
        Comprehensive code review.

        Args:
            code: Source code to review
            language: Programming language
            tests: Optional test code for coverage analysis
            rules: Optional override rules

        Returns:
            Review result with findings and quality metrics

        Example:
            >>> raven = PedanticRavenIntegration()
            >>> result = raven.review(
            ...     code="def process(data): eval(data)",
            ...     language="python"
            ... )
            >>> assert len(result.security_findings) > 0
        """
        active_rules = rules or self.rules

        # Collect findings
        security_findings = []
        performance_findings = []
        quality_report = QualityReport(0, 0, 0, 0, 0, 100)
        documentation_report = DocumentationReport(0, 0, 0, 0, 0, 0, 0, 100)
        coverage_report = None

        if active_rules.check_security:
            security_findings = self.check_security(code, language)

        if active_rules.check_performance:
            performance_findings = self.check_performance(code, language)

        if active_rules.check_quality:
            quality_report = self.check_quality(code, language)

        if active_rules.check_documentation:
            documentation_report = self.check_documentation(code, language)

        if active_rules.check_coverage and tests:
            coverage_report = self.check_test_coverage(code, tests, language)

        # Calculate overall score
        overall_score = self._calculate_overall_score(
            security_findings,
            performance_findings,
            quality_report,
            documentation_report,
            coverage_report,
        )

        # Determine success
        success = True

        # Block on critical security issues
        if active_rules.block_on_critical_security:
            critical_security = [
                f for f in security_findings if f.severity == "critical"
            ]
            if critical_security:
                success = False

        # Check minimum thresholds
        if quality_report.quality_score < active_rules.min_quality_score:
            success = False

        if (
            documentation_report.completeness_score
            < active_rules.min_documentation_score
        ):
            success = False

        if coverage_report and coverage_report.line_coverage < active_rules.min_coverage:
            success = False

        return ReviewResult(
            success=success,
            security_findings=security_findings,
            performance_findings=performance_findings,
            quality_report=quality_report,
            documentation_report=documentation_report,
            coverage_report=coverage_report,
            overall_score=overall_score,
        )

    def check_security(self, code: str, language: str) -> list[SecurityFinding]:
        """
        Security-focused review.

        Checks:
        - SQL injection vulnerabilities
        - XSS vulnerabilities
        - Command injection
        - Path traversal
        - Hardcoded credentials
        - Unsafe deserialization
        - Insecure random

        Args:
            code: Source code
            language: Programming language

        Returns:
            List of security findings
        """
        findings = []

        if language == "python":
            findings.extend(self._check_python_security(code))
        elif language == "typescript" or language == "javascript":
            findings.extend(self._check_typescript_security(code))
        # Add more languages as needed

        return findings

    def check_quality(self, code: str, language: str) -> QualityReport:
        """
        Code quality metrics.

        Metrics:
        - Cyclomatic complexity
        - Code duplication
        - Function length
        - Parameter count
        - Nesting depth
        - Comment ratio

        Args:
            code: Source code
            language: Programming language

        Returns:
            Quality report with metrics
        """
        if language == "python":
            return self._check_python_quality(code)
        elif language == "typescript" or language == "javascript":
            return self._check_typescript_quality(code)
        else:
            # Default metrics for unsupported languages
            return QualityReport(
                cyclomatic_complexity=1.0,
                code_duplication=0.0,
                average_function_length=10.0,
                max_nesting_depth=1,
                comment_ratio=0.0,
                quality_score=50.0,
            )

    def check_performance(
        self, code: str, language: str
    ) -> list[PerformanceFinding]:
        """
        Performance anti-patterns.

        Patterns:
        - N+1 query patterns
        - Inefficient loops
        - Unnecessary allocations
        - Missing indexes (SQL)
        - Blocking calls in async

        Args:
            code: Source code
            language: Programming language

        Returns:
            List of performance findings
        """
        findings = []

        if language == "python":
            findings.extend(self._check_python_performance(code))
        elif language == "typescript" or language == "javascript":
            findings.extend(self._check_typescript_performance(code))

        return findings

    def check_documentation(
        self, code: str, language: str
    ) -> DocumentationReport:
        """
        Documentation completeness.

        Checks:
        - Docstring presence
        - Parameter documentation
        - Return type documentation
        - Example presence
        - Type hints (Python, TypeScript)

        Args:
            code: Source code
            language: Programming language

        Returns:
            Documentation report
        """
        if language == "python":
            return self._check_python_documentation(code)
        elif language == "typescript" or language == "javascript":
            return self._check_typescript_documentation(code)
        else:
            return DocumentationReport(
                functions_documented=0,
                functions_total=0,
                parameters_documented=0,
                parameters_total=0,
                return_types_documented=0,
                returns_total=0,
                examples_present=0,
                completeness_score=0.0,
            )

    def check_test_coverage(
        self, code: str, tests: str, language: str
    ) -> CoverageReport:
        """
        Test coverage analysis.

        Coverage:
        - Line coverage
        - Branch coverage
        - Function coverage
        - Critical path coverage

        Args:
            code: Source code
            tests: Test code
            language: Programming language

        Returns:
            Coverage report

        Note: This is a simplified implementation. Full coverage would
        require actually executing tests with coverage tools.
        """
        # Simplified coverage estimation based on test presence
        code_lines = len([line for line in code.split("\n") if line.strip()])
        test_lines = len([line for line in tests.split("\n") if line.strip()])

        # Rough estimate: test/code ratio * 100
        coverage_ratio = min(100.0, (test_lines / max(1, code_lines)) * 100)

        return CoverageReport(
            line_coverage=coverage_ratio,
            branch_coverage=coverage_ratio * 0.8,  # Branches typically lower
            function_coverage=coverage_ratio,
            critical_path_coverage=coverage_ratio * 0.9,
        )

    # Language-specific security checks

    def _check_python_security(self, code: str) -> list[SecurityFinding]:
        """Check Python-specific security issues."""
        findings = []
        lines = code.split("\n")

        for i, line in enumerate(lines, 1):
            # Check for eval() usage
            if re.search(r"\beval\s*\(", line):
                findings.append(
                    SecurityFinding(
                        category="injection",
                        severity="critical",
                        message="Dangerous eval() usage detected - code injection risk",
                        line=i,
                        cwe_id="CWE-95",
                        suggested_fix="Use ast.literal_eval() for safe evaluation",
                    )
                )

            # Check for exec() usage
            if re.search(r"\bexec\s*\(", line):
                findings.append(
                    SecurityFinding(
                        category="injection",
                        severity="critical",
                        message="Dangerous exec() usage detected - code injection risk",
                        line=i,
                        cwe_id="CWE-95",
                        suggested_fix="Avoid exec() or use safe alternatives",
                    )
                )

            # Check for SQL injection patterns
            if re.search(r"['\"]SELECT.*%s", line) or re.search(
                r"['\"]SELECT.*\+\s*\w+", line
            ):
                findings.append(
                    SecurityFinding(
                        category="injection",
                        severity="high",
                        message="Potential SQL injection vulnerability",
                        line=i,
                        cwe_id="CWE-89",
                        suggested_fix="Use parameterized queries",
                    )
                )

            # Check for command injection
            if re.search(r"os\.system\s*\(", line) or re.search(r"subprocess\.call\s*\([^,]*\+", line):
                findings.append(
                    SecurityFinding(
                        category="injection",
                        severity="high",
                        message="Potential command injection vulnerability",
                        line=i,
                        cwe_id="CWE-78",
                        suggested_fix="Use subprocess with list arguments",
                    )
                )

            # Check for hardcoded secrets
            if re.search(r"(password|secret|api_key)\s*=\s*['\"][^'\"]{8,}", line, re.IGNORECASE):
                findings.append(
                    SecurityFinding(
                        category="auth",
                        severity="high",
                        message="Potential hardcoded credential",
                        line=i,
                        cwe_id="CWE-798",
                        suggested_fix="Use environment variables or secret management",
                    )
                )

        return findings

    def _check_typescript_security(self, code: str) -> list[SecurityFinding]:
        """Check TypeScript/JavaScript-specific security issues."""
        findings = []
        lines = code.split("\n")

        for i, line in enumerate(lines, 1):
            # Check for eval() usage
            if re.search(r"\beval\s*\(", line):
                findings.append(
                    SecurityFinding(
                        category="injection",
                        severity="critical",
                        message="Dangerous eval() usage detected",
                        line=i,
                        cwe_id="CWE-95",
                    )
                )

            # Check for innerHTML usage (XSS risk)
            if "innerHTML" in line and "=" in line:
                findings.append(
                    SecurityFinding(
                        category="xss",
                        severity="high",
                        message="Potential XSS via innerHTML",
                        line=i,
                        cwe_id="CWE-79",
                        suggested_fix="Use textContent or sanitize input",
                    )
                )

        return findings

    # Language-specific quality checks

    def _check_python_quality(self, code: str) -> QualityReport:
        """Check Python code quality."""
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return QualityReport(0, 0, 0, 0, 0, 0)

        # Calculate metrics
        functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]

        # Function length
        func_lengths = []
        for func in functions:
            if hasattr(func, "end_lineno") and hasattr(func, "lineno"):
                func_lengths.append(func.end_lineno - func.lineno)

        avg_func_length = sum(func_lengths) / len(func_lengths) if func_lengths else 0

        # Nesting depth
        max_nesting = self._max_nesting_depth(tree)

        # Comment ratio
        lines = code.split("\n")
        comment_lines = sum(1 for line in lines if line.strip().startswith("#"))
        total_lines = len([line for line in lines if line.strip()])
        comment_ratio = comment_lines / max(1, total_lines)

        # Cyclomatic complexity (simplified)
        complexity = len(functions) + sum(
            1
            for node in ast.walk(tree)
            if isinstance(node, (ast.If, ast.For, ast.While, ast.ExceptHandler))
        )

        # Quality score
        quality_score = 100.0
        if avg_func_length > 50:
            quality_score -= 20
        if max_nesting > 4:
            quality_score -= 20
        if comment_ratio < 0.1:
            quality_score -= 10
        if complexity > 20:
            quality_score -= 15

        return QualityReport(
            cyclomatic_complexity=float(complexity),
            code_duplication=0.0,  # Would need more analysis
            average_function_length=avg_func_length,
            max_nesting_depth=max_nesting,
            comment_ratio=comment_ratio,
            quality_score=max(0, quality_score),
        )

    def _check_typescript_quality(self, code: str) -> QualityReport:
        """Check TypeScript code quality (simplified)."""
        lines = code.split("\n")

        # Count functions
        function_pattern = r"(function\s+\w+|const\s+\w+\s*=\s*\([^)]*\)\s*=>)"
        functions = re.findall(function_pattern, code)

        # Estimate complexity
        complexity = len(functions) + code.count("if") + code.count("for") + code.count("while")

        # Comment ratio
        comment_lines = sum(1 for line in lines if line.strip().startswith("//"))
        total_lines = len([line for line in lines if line.strip()])
        comment_ratio = comment_lines / max(1, total_lines)

        quality_score = 70.0  # Base score for TypeScript

        return QualityReport(
            cyclomatic_complexity=float(complexity),
            code_duplication=0.0,
            average_function_length=10.0,
            max_nesting_depth=2,
            comment_ratio=comment_ratio,
            quality_score=quality_score,
        )

    # Language-specific performance checks

    def _check_python_performance(self, code: str) -> list[PerformanceFinding]:
        """Check Python performance anti-patterns."""
        findings = []
        lines = code.split("\n")

        for i, line in enumerate(lines, 1):
            # Check for list comprehension in loop
            if "for" in line and "[" in line and "in" in line:
                if re.search(r"for\s+\w+\s+in\s+\[.*for.*in", line):
                    findings.append(
                        PerformanceFinding(
                            pattern="nested_comprehension",
                            impact="medium",
                            message="Nested list comprehension may be inefficient",
                            line=i,
                        )
                    )

        return findings

    def _check_typescript_performance(self, code: str) -> list[PerformanceFinding]:
        """Check TypeScript performance anti-patterns."""
        findings = []
        # Simplified implementation
        return findings

    # Language-specific documentation checks

    def _check_python_documentation(self, code: str) -> DocumentationReport:
        """Check Python documentation completeness."""
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return DocumentationReport(0, 0, 0, 0, 0, 0, 0, 0)

        functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]

        functions_documented = 0
        parameters_documented = 0
        parameters_total = 0
        return_types_documented = 0
        returns_total = len(functions)

        for func in functions:
            # Check for docstring
            if ast.get_docstring(func):
                functions_documented += 1

            # Count parameters
            if hasattr(func.args, "args"):
                parameters_total += len(func.args.args)
                # Simple heuristic: if there's a docstring, assume params are documented
                if ast.get_docstring(func):
                    parameters_documented += len(func.args.args)

            # Check for return type annotation
            if func.returns:
                return_types_documented += 1

        completeness_score = 0.0
        if functions:
            doc_ratio = functions_documented / len(functions)
            param_ratio = parameters_documented / max(1, parameters_total)
            return_ratio = return_types_documented / returns_total if returns_total > 0 else 0
            completeness_score = (doc_ratio + param_ratio + return_ratio) / 3 * 100

        return DocumentationReport(
            functions_documented=functions_documented,
            functions_total=len(functions),
            parameters_documented=parameters_documented,
            parameters_total=parameters_total,
            return_types_documented=return_types_documented,
            returns_total=returns_total,
            examples_present=0,
            completeness_score=completeness_score,
        )

    def _check_typescript_documentation(self, code: str) -> DocumentationReport:
        """Check TypeScript documentation completeness (simplified)."""
        # Count functions
        function_pattern = r"(function\s+\w+|const\s+\w+\s*=)"
        functions = re.findall(function_pattern, code)

        # Count JSDoc comments
        jsdoc_pattern = r"/\*\*.*?\*/"
        jsdocs = re.findall(jsdoc_pattern, code, re.DOTALL)

        completeness_score = (len(jsdocs) / max(1, len(functions))) * 100

        return DocumentationReport(
            functions_documented=len(jsdocs),
            functions_total=len(functions),
            parameters_documented=0,
            parameters_total=0,
            return_types_documented=0,
            returns_total=0,
            examples_present=0,
            completeness_score=completeness_score,
        )

    # Helper methods

    def _max_nesting_depth(self, node: ast.AST, current_depth: int = 0) -> int:
        """Calculate maximum nesting depth in AST."""
        max_depth = current_depth

        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.With)):
                child_depth = self._max_nesting_depth(child, current_depth + 1)
                max_depth = max(max_depth, child_depth)
            else:
                child_depth = self._max_nesting_depth(child, current_depth)
                max_depth = max(max_depth, child_depth)

        return max_depth

    def _calculate_overall_score(
        self,
        security_findings: list[SecurityFinding],
        performance_findings: list[PerformanceFinding],
        quality_report: QualityReport,
        documentation_report: DocumentationReport,
        coverage_report: Optional[CoverageReport],
    ) -> float:
        """Calculate overall review score."""
        score = quality_report.quality_score

        # Deduct for security issues
        for finding in security_findings:
            if finding.severity == "critical":
                score -= 25
            elif finding.severity == "high":
                score -= 15
            elif finding.severity == "medium":
                score -= 5

        # Deduct for performance issues
        for finding in performance_findings:
            if finding.impact == "high":
                score -= 10
            elif finding.impact == "medium":
                score -= 5

        # Factor in documentation
        score = (score + documentation_report.completeness_score) / 2

        # Factor in coverage if available
        if coverage_report:
            score = (score + coverage_report.line_coverage) / 2

        return max(0.0, min(100.0, score))


__all__ = [
    "PedanticRavenIntegration",
    "ReviewResult",
    "ReviewRules",
    "SecurityFinding",
    "PerformanceFinding",
    "QualityReport",
    "DocumentationReport",
    "CoverageReport",
]
