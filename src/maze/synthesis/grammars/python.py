"""
Python grammar templates for constrained code generation.

Provides Lark grammar templates for common Python constructs.

CRITICAL: These grammars are designed for llguidance (vLLM V1 backend).
Key requirements:
- NO inline rules (?start:) - llguidance doesn't support them
- Use "start:" not "?start:"
- Stick to standard Lark syntax (no fancy features)

See docs/GRAMMAR_CONSTRAINTS.md for details.
"""

from maze.synthesis.grammar_builder import GrammarTemplate

# Basic Python function grammar
PYTHON_FUNCTION = GrammarTemplate(
    name="python_function",
    language="python",
    description="Grammar for Python function definitions",
    grammar="""
start: function_def

function_def: decorators? async_modifier? "def" IDENT "(" parameters? ")" return_annotation? ":" suite

decorators: ("@" dotted_name "(" args? ")" NEWLINE)+
dotted_name: IDENT ("." IDENT)*

async_modifier: "async"

parameters: param ("," param)* ("," "/")?  ("," "*" param)? ("," "**" param)?
          | "*" param ("," param)* ("," "**" param)?
          | "**" param

param: IDENT type_annotation? default?
type_annotation: ":" type_expr
default: "=" expression

return_annotation: "->" type_expr

suite: simple_stmt | NEWLINE INDENT statement+ DEDENT

statement: simple_stmt | compound_stmt

simple_stmt: (expr_stmt | return_stmt | pass_stmt | break_stmt | continue_stmt | assign_stmt) NEWLINE

compound_stmt: if_stmt | while_stmt | for_stmt | try_stmt | with_stmt | funcdef

expr_stmt: expression
return_stmt: "return" expression?
pass_stmt: "pass"
break_stmt: "break"
continue_stmt: "continue"
assign_stmt: target "=" expression
           | target ":" type_expr ("=" expression)?

target: IDENT | attribute | subscription

if_stmt: "if" expression ":" suite ("elif" expression ":" suite)* ("else" ":" suite)?
while_stmt: "while" expression ":" suite
for_stmt: "for" target "in" expression ":" suite
try_stmt: "try" ":" suite except_clause+ (else_clause)? (finally_clause)?
except_clause: "except" expression? ("as" IDENT)? ":" suite
else_clause: "else" ":" suite
finally_clause: "finally" ":" suite
with_stmt: "with" with_item ("," with_item)* ":" suite
with_item: expression ("as" target)?

funcdef: function_def

expression: literal
          | IDENT
          | call
          | attribute
          | subscription
          | binary_op
          | unary_op
          | comparison
          | lambda_expr
          | dict_expr
          | list_expr
          | tuple_expr
          | set_expr
          | f_string

call: expression "(" args? ")"
args: argument ("," argument)*
argument: expression | IDENT "=" expression

attribute: expression "." IDENT
subscription: expression "[" expression "]"

binary_op: expression ("+" | "-" | "*" | "/" | "//" | "%" | "**" | "@" | "&" | "|" | "^" | "<<" | ">>") expression
unary_op: ("+" | "-" | "~" | "not") expression
comparison: expression ("==" | "!=" | "<" | ">" | "<=" | ">=" | "is" | "is not" | "in" | "not in") expression

lambda_expr: "lambda" parameters? ":" expression

dict_expr: "{" dict_items? "}"
dict_items: dict_item ("," dict_item)* ","?
dict_item: expression ":" expression | "**" expression

list_expr: "[" list_items? "]"
list_items: expression ("," expression)* ","?

tuple_expr: "(" tuple_items? ")"
tuple_items: expression ("," expression)+ ","?
           | expression ","

set_expr: "{" set_items "}"
set_items: expression ("," expression)+ ","?

f_string: "f\"" f_string_parts "\""
        | "f'" f_string_parts "'"
f_string_parts: (f_string_text | f_string_replacement)*
f_string_text: /[^{}"']+/
f_string_replacement: "{" expression "}"

literal: NUMBER | STRING | BOOLEAN | NONE

type_expr: basic_type
         | generic_type
         | union_type
         | optional_type

basic_type: "int" | "str" | "float" | "bool" | "bytes" | "None" | "Any" | IDENT
generic_type: IDENT "[" type_args "]"
type_args: type_expr ("," type_expr)*
union_type: type_expr "|" type_expr ("|" type_expr)*
optional_type: type_expr "| None"

IDENT: /[a-zA-Z_][a-zA-Z0-9_]*/
NUMBER: /-?\\d+(\\.\\d+)?([eE][+-]?\\d+)?/ | /-?0[xX][0-9a-fA-F]+/ | /-?0[oO][0-7]+/ | /-?0[bB][01]+/
STRING: /"([^"\\\\]|\\\\.)*"/ | /'([^'\\\\]|\\\\.)*'/ | /\"\"\"[\\s\\S]*?\"\"\"/ | /'''[\\s\\S]*?'''/
BOOLEAN: "True" | "False"
NONE: "None"

NEWLINE: /\\r?\\n/
INDENT: /<INDENT>/
DEDENT: /<DEDENT>/

%ignore /[ \\t]+/
%ignore /#.*/
""",
)

# Class definition grammar
PYTHON_CLASS = GrammarTemplate(
    name="python_class",
    language="python",
    description="Grammar for Python class definitions",
    grammar="""
start: class_def

class_def: decorators? "class" IDENT type_params? bases? ":" suite

decorators: ("@" dotted_name "(" args? ")" NEWLINE)+
dotted_name: IDENT ("." IDENT)*

type_params: "[" type_param ("," type_param)* "]"
type_param: IDENT type_bound?
type_bound: ":" type_expr

bases: "(" base_list? ")"
base_list: base ("," base)*
base: expression

suite: simple_stmt | NEWLINE INDENT class_member+ DEDENT

class_member: method_def | field_def | pass_stmt NEWLINE

method_def: decorators? async_modifier? "def" IDENT "(" parameters? ")" return_annotation? ":" method_suite
async_modifier: "async"
parameters: param ("," param)*
param: IDENT type_annotation? default?
type_annotation: ":" type_expr
default: "=" expression
return_annotation: "->" type_expr
method_suite: simple_stmt | NEWLINE INDENT statement+ DEDENT

field_def: IDENT ":" type_expr ("=" expression)? NEWLINE

statement: simple_stmt | compound_stmt
simple_stmt: (expr_stmt | return_stmt | pass_stmt) NEWLINE
compound_stmt: if_stmt | for_stmt | while_stmt

expr_stmt: expression
return_stmt: "return" expression?
pass_stmt: "pass"

if_stmt: "if" expression ":" suite ("elif" expression ":" suite)* ("else" ":" suite)?
for_stmt: "for" IDENT "in" expression ":" suite
while_stmt: "while" expression ":" suite

expression: literal | IDENT | call | attribute | binary_op
call: expression "(" args? ")"
args: argument ("," argument)*
argument: expression | IDENT "=" expression
attribute: expression "." IDENT
binary_op: expression ("+" | "-" | "*" | "/") expression

literal: NUMBER | STRING | BOOLEAN | NONE

type_expr: IDENT | generic_type | union_type
generic_type: IDENT "[" type_args "]"
type_args: type_expr ("," type_expr)*
union_type: type_expr "|" type_expr

IDENT: /[a-zA-Z_][a-zA-Z0-9_]*/
NUMBER: /-?\\d+(\\.\\d+)?/
STRING: /"([^"\\\\]|\\\\.)*"/ | /'([^'\\\\]|\\\\.)*'/
BOOLEAN: "True" | "False"
NONE: "None"

NEWLINE: /\\r?\\n/
INDENT: /<INDENT>/
DEDENT: /<DEDENT>/

%ignore /[ \\t]+/
%ignore /#.*/
""",
)

# Module-level grammar (for complete files)
PYTHON_MODULE = GrammarTemplate(
    name="python_module",
    language="python",
    description="Grammar for complete Python modules",
    grammar="""
start: module

module: (import_stmt | statement)*

import_stmt: import_name | import_from
import_name: "import" dotted_as_names NEWLINE
import_from: "from" (dots? dotted_name | dots) "import" import_as_names NEWLINE

dotted_as_names: dotted_as_name ("," dotted_as_name)*
dotted_as_name: dotted_name ("as" IDENT)?
dotted_name: IDENT ("." IDENT)*

import_as_names: import_as_name ("," import_as_name)*
import_as_name: IDENT ("as" IDENT)?

dots: "."+

statement: simple_stmt | compound_stmt

simple_stmt: (expr_stmt | assign_stmt) NEWLINE
compound_stmt: function_def | class_def | if_stmt | for_stmt | while_stmt

expr_stmt: expression
assign_stmt: IDENT ":" type_expr ("=" expression)?
           | IDENT "=" expression

function_def: "def" IDENT "(" parameters? ")" return_annotation? ":" suite
parameters: IDENT ("," IDENT)*
return_annotation: "->" type_expr
suite: simple_stmt | NEWLINE INDENT statement+ DEDENT

class_def: "class" IDENT bases? ":" class_suite
bases: "(" IDENT ("," IDENT)* ")"
class_suite: "pass" NEWLINE | NEWLINE INDENT class_member+ DEDENT
class_member: function_def | assign_stmt NEWLINE

if_stmt: "if" expression ":" suite
for_stmt: "for" IDENT "in" expression ":" suite
while_stmt: "while" expression ":" suite

expression: IDENT | literal | call
call: IDENT "(" args? ")"
args: expression ("," expression)*

literal: NUMBER | STRING | BOOLEAN | NONE

type_expr: IDENT

IDENT: /[a-zA-Z_][a-zA-Z0-9_]*/
NUMBER: /-?\\d+(\\.\\d+)?/
STRING: /"([^"\\\\]|\\\\.)*"/ | /'([^'\\\\]|\\\\.)*'/
BOOLEAN: "True" | "False"
NONE: "None"

NEWLINE: /\\r?\\n/
INDENT: /<INDENT>/
DEDENT: /<DEDENT>/

%ignore /[ \\t]+/
%ignore /#.*/
""",
)

# Function BODY grammar (for completing partial signatures)
# USE CASE: Code completion where prompt already has signature
#   Prompt: "def calculate_sum(a: int, b: int) -> int:"
#   This grammar generates ONLY the body (suite), not the signature
# WHEN TO USE: Prompt ends with ":" (Python function/class signature)
# WHEN NOT TO USE: Full generation from description - use PYTHON_FUNCTION instead
PYTHON_FUNCTION_BODY = GrammarTemplate(
    name="python_function_body",
    language="python",
    description="Grammar for Python function body (completion after signature)",
    grammar="""
start: suite

suite: simple_stmt | NEWLINE INDENT statement+ DEDENT

statement: simple_stmt | compound_stmt

simple_stmt: (expr_stmt | return_stmt | pass_stmt | break_stmt | continue_stmt | assign_stmt) NEWLINE

compound_stmt: if_stmt | while_stmt | for_stmt | try_stmt | with_stmt

expr_stmt: expression
return_stmt: "return" expression?
pass_stmt: "pass"
break_stmt: "break"
continue_stmt: "continue"
assign_stmt: target "=" expression
           | target ":" type_expr ("=" expression)?

target: IDENT | attribute | subscription

if_stmt: "if" expression ":" suite ("elif" expression ":" suite)* ("else" ":" suite)?
while_stmt: "while" expression ":" suite
for_stmt: "for" target "in" expression ":" suite
try_stmt: "try" ":" suite except_clause+ (else_clause)? (finally_clause)?
except_clause: "except" expression? ("as" IDENT)? ":" suite
else_clause: "else" ":" suite
finally_clause: "finally" ":" suite
with_stmt: "with" with_item ("," with_item)* ":" suite
with_item: expression ("as" target)?

expression: literal
          | IDENT
          | call
          | attribute
          | subscription
          | binary_op
          | unary_op
          | comparison
          | lambda_expr
          | dict_expr
          | list_expr
          | tuple_expr
          | set_expr
          | f_string

call: expression "(" args? ")"
args: argument ("," argument)*
argument: expression | IDENT "=" expression

attribute: expression "." IDENT
subscription: expression "[" expression "]"

binary_op: expression ("+" | "-" | "*" | "/" | "//" | "%" | "**" | "@" | "&" | "|" | "^" | "<<" | ">>") expression
unary_op: ("+" | "-" | "~" | "not") expression
comparison: expression ("==" | "!=" | "<" | ">" | "<=" | ">=" | "is" | "is not" | "in" | "not in") expression

lambda_expr: "lambda" parameters? ":" expression
parameters: IDENT ("," IDENT)*

dict_expr: "{" dict_items? "}"
dict_items: dict_item ("," dict_item)* ","?
dict_item: expression ":" expression | "**" expression

list_expr: "[" list_items? "]"
list_items: expression ("," expression)* ","?

tuple_expr: "(" tuple_items? ")"
tuple_items: expression ("," expression)+ ","?
           | expression ","

set_expr: "{" set_items "}"
set_items: expression ("," expression)+ ","?

f_string: "f\\"" f_string_parts "\\""
        | "f'" f_string_parts "'"
f_string_parts: (f_string_text | f_string_replacement)*
f_string_text: /[^{}"']+/
f_string_replacement: "{" expression "}"

literal: NUMBER | STRING | BOOLEAN | NONE

type_expr: basic_type
         | generic_type
         | union_type
         | optional_type

basic_type: "int" | "str" | "float" | "bool" | "bytes" | "None" | "Any" | IDENT
generic_type: IDENT "[" type_args "]"
type_args: type_expr ("," type_expr)*
union_type: type_expr "|" type_expr ("|" type_expr)*
optional_type: type_expr "| None"

IDENT: /[a-zA-Z_][a-zA-Z0-9_]*/
NUMBER: /-?\\d+(\\.\\d+)?([eE][+-]?\\d+)?/ | /-?0[xX][0-9a-fA-F]+/ | /-?0[oO][0-7]+/ | /-?0[bB][01]+/
STRING: /"([^"\\\\]|\\\\.)*"/ | /'([^'\\\\]|\\\\.)*'/ | /\\"\\"\\"[\\s\\S]*?\\"\\"\\"/ | /'''[\\s\\S]*?'''/
BOOLEAN: "True" | "False"
NONE: "None"

NEWLINE: /\\r?\\n/
INDENT: /<INDENT>/
DEDENT: /<DEDENT>/

%ignore /[ \\t]+/
%ignore /#.*/
""",
)

# Export all templates
ALL_TEMPLATES = [
    PYTHON_FUNCTION,
    PYTHON_FUNCTION_BODY,
    PYTHON_CLASS,
    PYTHON_MODULE,
]

__all__ = [
    "PYTHON_FUNCTION",
    "PYTHON_FUNCTION_BODY",
    "PYTHON_CLASS",
    "PYTHON_MODULE",
    "ALL_TEMPLATES",
]
