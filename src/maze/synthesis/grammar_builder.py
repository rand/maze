"""
Grammar builder for constructing Lark grammars from templates.

This module provides utilities for building Lark grammars programmatically,
supporting templates, composition, and JSON Schema embedding.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class GrammarTemplate:
    """
    A reusable grammar template with variable substitution.

    Templates support variable substitution using {{variable}} syntax
    and can be composed with other templates.
    """

    name: str
    grammar: str
    variables: set[str] = field(default_factory=set)
    language: str = "generic"
    description: str = ""

    def __post_init__(self):
        """Extract variables from grammar template."""
        if not self.variables:
            # Find all {{variable}} patterns
            self.variables = set(re.findall(r"\{\{(\w+)\}\}", self.grammar))

    def render(self, **kwargs) -> str:
        """
        Render template with variable substitution.

        Args:
            **kwargs: Variable assignments

        Returns:
            Rendered grammar string

        Raises:
            ValueError: If required variables are missing
        """
        missing = self.variables - set(kwargs.keys())
        if missing:
            raise ValueError(f"Missing required variables: {missing}")

        rendered = self.grammar
        for var, value in kwargs.items():
            rendered = rendered.replace(f"{{{{{var}}}}}", str(value))

        return rendered


class GrammarBuilder:
    """
    Builder for constructing Lark grammars programmatically.

    Supports:
    - Template loading and management
    - Grammar composition
    - JSON Schema embedding (%json directive)
    - Rule deduplication and validation
    """

    def __init__(self, language: str = "generic"):
        """
        Initialize grammar builder.

        Args:
            language: Target language for grammar
        """
        self.language = language
        self.templates: dict[str, GrammarTemplate] = {}
        self.rules: list[str] = []
        self.terminals: list[str] = []
        self.directives: list[str] = []
        self.imports: list[str] = []

    def add_template(self, template: GrammarTemplate) -> GrammarBuilder:
        """
        Register a grammar template.

        Args:
            template: Template to register

        Returns:
            Self for chaining
        """
        self.templates[template.name] = template
        logger.debug(
            f"Registered template '{template.name}' with {len(template.variables)} variables"
        )
        return self

    def load_template(self, name: str, **kwargs) -> GrammarBuilder:
        """
        Load and render a template into the grammar.

        Args:
            name: Template name
            **kwargs: Variable assignments for rendering

        Returns:
            Self for chaining

        Raises:
            KeyError: If template not found
        """
        if name not in self.templates:
            raise KeyError(f"Template '{name}' not found. Available: {list(self.templates.keys())}")

        template = self.templates[name]
        rendered = template.render(**kwargs)

        # Parse rendered grammar and add components
        self._parse_and_add(rendered)

        return self

    def add_rule(self, name: str, production: str, priority: str | None = None) -> GrammarBuilder:
        """
        Add a grammar rule.

        Args:
            name: Rule name
            production: Rule production
            priority: Optional priority modifier (?, !, etc.)

        Returns:
            Self for chaining
        """
        prefix = priority if priority else ""
        rule = f"{prefix}{name}: {production}"

        if rule not in self.rules:
            self.rules.append(rule)

        return self

    def add_terminal(self, name: str, pattern: str) -> GrammarBuilder:
        """
        Add a terminal definition.

        Args:
            name: Terminal name (uppercase)
            pattern: Regex pattern

        Returns:
            Self for chaining
        """
        terminal = f"{name}: {pattern}"

        if terminal not in self.terminals:
            self.terminals.append(terminal)

        return self

    def add_json_schema(
        self, schema: dict[str, Any], rule_name: str = "json_value"
    ) -> GrammarBuilder:
        """
        Embed JSON Schema using %json directive.

        Args:
            schema: JSON Schema dict
            rule_name: Name for the rule that uses this schema

        Returns:
            Self for chaining
        """
        # Format schema as compact JSON
        schema_json = json.dumps(schema, separators=(",", ":"))

        # Add rule with %json directive
        json_rule = f"{rule_name}: %json {schema_json}"

        if json_rule not in self.rules:
            self.rules.append(json_rule)

        return self

    def add_directive(self, directive: str) -> GrammarBuilder:
        """
        Add a grammar directive (e.g., %ignore, %import).

        Args:
            directive: Directive string

        Returns:
            Self for chaining
        """
        if directive not in self.directives:
            self.directives.append(directive)

        return self

    def ignore_whitespace(self) -> GrammarBuilder:
        """
        Add standard whitespace ignore directive.

        Returns:
            Self for chaining
        """
        return self.add_directive("%ignore /\\s+/")

    def _parse_and_add(self, grammar: str) -> None:
        """
        Parse grammar string and add rules, terminals, directives.

        Args:
            grammar: Grammar string to parse
        """
        lines = grammar.strip().split("\n")

        for line in lines:
            line = line.strip()
            if not line or line.startswith("//") or line.startswith("#"):
                continue

            # Directives
            if line.startswith("%"):
                if line not in self.directives:
                    self.directives.append(line)

            # Terminals (uppercase name)
            elif ":" in line:
                parts = line.split(":", 1)
                name = parts[0].strip().lstrip("?!")

                if name and name[0].isupper():
                    if line not in self.terminals:
                        self.terminals.append(line)
                else:
                    if line not in self.rules:
                        self.rules.append(line)

    def build(self) -> str:
        """
        Build final grammar string.

        Returns:
            Complete Lark grammar
        """
        parts = []

        # Add imports
        if self.imports:
            parts.extend(self.imports)
            parts.append("")

        # Add rules
        if self.rules:
            parts.extend(self.rules)
            parts.append("")

        # Add terminals
        if self.terminals:
            parts.extend(self.terminals)
            parts.append("")

        # Add directives
        if self.directives:
            parts.extend(self.directives)

        return "\n".join(parts).strip()

    def validate(self) -> tuple[bool, str | None]:
        """
        Validate grammar structure.

        Returns:
            (is_valid, error_message)
        """
        # Check for start rule
        has_start = any(
            line.strip().startswith("?start:") or line.strip().startswith("start:")
            for line in self.rules
        )

        if not has_start:
            return False, "Grammar must have a 'start' rule"

        # Check for basic syntax
        for rule in self.rules:
            if ":" not in rule:
                return False, f"Invalid rule syntax: {rule}"

        return True, None

    def clear(self) -> GrammarBuilder:
        """
        Clear all rules, terminals, and directives.

        Returns:
            Self for chaining
        """
        self.rules.clear()
        self.terminals.clear()
        self.directives.clear()
        self.imports.clear()
        return self


def create_json_schema_grammar(schema: dict[str, Any], start_rule: str = "start") -> str:
    """
    Create a complete grammar from a JSON Schema.

    Args:
        schema: JSON Schema dict
        start_rule: Name of start rule

    Returns:
        Complete Lark grammar string
    """
    builder = GrammarBuilder()
    builder.add_rule(start_rule, "json_value", priority="?")
    builder.add_json_schema(schema, "json_value")
    builder.ignore_whitespace()

    return builder.build()


def merge_grammars(*grammars: str) -> str:
    """
    Merge multiple grammar strings, deduplicating rules.

    Args:
        *grammars: Grammar strings to merge

    Returns:
        Merged grammar
    """
    builder = GrammarBuilder()

    for grammar in grammars:
        builder._parse_and_add(grammar)

    return builder.build()


__all__ = [
    "GrammarBuilder",
    "GrammarTemplate",
    "create_json_schema_grammar",
    "merge_grammars",
]
