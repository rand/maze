"""
TypeScript grammar templates for constrained code generation.

Provides Lark grammar templates for common TypeScript constructs.
"""

from maze.synthesis.grammar_builder import GrammarTemplate

# Basic TypeScript function grammar
TYPESCRIPT_FUNCTION = GrammarTemplate(
    name="typescript_function",
    language="typescript",
    description="Grammar for TypeScript function declarations",
    grammar="""
start: function_decl

function_decl: export_modifier? async_modifier? "function" IDENT type_params? "(" params? ")" return_type? block

export_modifier: "export" "default"?
async_modifier: "async"

type_params: "<" type_param ("," type_param)* ">"
type_param: IDENT type_constraint?
type_constraint: "extends" type_expr

params: param ("," param)*
param: param_modifier? IDENT optional_marker? ":" type_expr default_value?
param_modifier: "public" | "private" | "protected" | "readonly"
optional_marker: "?"
default_value: "=" expression

return_type: ":" type_expr

block: "{" statement* "}"

statement: return_stmt
         | var_decl
         | expr_stmt
         | if_stmt
         | for_stmt
         | while_stmt

return_stmt: "return" expression? ";"
var_decl: const_var | let_var
const_var: "const" IDENT type_annotation? "=" expression ";"
let_var: "let" IDENT type_annotation? ("=" expression)? ";"
type_annotation: ":" type_expr
expr_stmt: expression ";"

if_stmt: "if" "(" expression ")" block ("else" block)?
for_stmt: "for" "(" for_init? ";" expression? ";" expression? ")" block
for_init: var_decl | expression
while_stmt: "while" "(" expression ")" block

expression: literal
          | IDENT
          | call_expr
          | member_expr
          | binary_expr
          | unary_expr
          | paren_expr
          | template_literal
          | object_literal
          | array_literal
          | arrow_function

call_expr: expression "(" args? ")"
args: expression ("," expression)*

member_expr: expression "." IDENT
           | expression "[" expression "]"

binary_expr: expression binary_op expression
binary_op: "+" | "-" | "*" | "/" | "%" | "===" | "!==" | "==" | "!=" | "<" | ">" | "<=" | ">=" | "&&" | "||" | "??" | "&" | "|"

unary_expr: unary_op expression
unary_op: "!" | "-" | "+" | "typeof" | "void" | "await"

paren_expr: "(" expression ")"

template_literal: "`" template_part* "`"
template_part: /[^`$]+/ | "${" expression "}"

object_literal: "{" object_props? "}"
object_props: object_prop ("," object_prop)* ","?
object_prop: IDENT ":" expression
           | IDENT

array_literal: "[" array_elements? "]"
array_elements: expression ("," expression)* ","?

arrow_function: arrow_params "=>" (block | expression)
arrow_params: IDENT | "(" params? ")"

literal: NUMBER | STRING | BOOLEAN | NULL | UNDEFINED

type_expr: basic_type
         | union_type
         | generic_type
         | function_type
         | object_type
         | array_type
         | tuple_type

basic_type: "string" | "number" | "boolean" | "any" | "void" | "never" | "unknown" | IDENT
union_type: type_expr ("|" type_expr)+
generic_type: IDENT "<" type_args ">"
type_args: type_expr ("," type_expr)*
function_type: "(" function_params? ")" "=>" type_expr
function_params: function_param ("," function_param)*
function_param: IDENT ":" type_expr
object_type: "{" object_type_members? "}"
object_type_members: object_type_member ("," object_type_member)* ","?
object_type_member: IDENT optional_marker? ":" type_expr
array_type: type_expr "[" "]"
tuple_type: "[" type_expr ("," type_expr)* "]"

IDENT: /[a-zA-Z_$][a-zA-Z0-9_$]*/
NUMBER: /-?\\d+(\\.\\d+)?([eE][+-]?\\d+)?/
STRING: /"([^"\\\\]|\\\\.)*"/ | /'([^'\\\\]|\\\\.)*'/
BOOLEAN: "true" | "false"
NULL: "null"
UNDEFINED: "undefined"

%ignore /\\s+/
%ignore /\\/\\/.*/
%ignore /\\/\\*[\\s\\S]*?\\*\\//
""",
)

# Interface grammar
TYPESCRIPT_INTERFACE = GrammarTemplate(
    name="typescript_interface",
    language="typescript",
    description="Grammar for TypeScript interface declarations",
    grammar=r"""
start: interface_decl

interface_decl: export_modifier? "interface" IDENT type_params? extends_clause? "{" interface_members? "}"

export_modifier: "export"

type_params: "<" type_param ("," type_param)* ">"
type_param: IDENT type_constraint?
type_constraint: "extends" type_expr

extends_clause: "extends" type_list
type_list: type_expr ("," type_expr)*

interface_members: interface_member+
interface_member: property_sig
                | method_sig
                | index_sig

property_sig: readonly_modifier? IDENT optional_marker? ":" type_expr ";"?
readonly_modifier: "readonly"
optional_marker: "?"

method_sig: IDENT type_params? "(" params? ")" return_type? ";"?
params: param ("," param)*
param: IDENT optional_marker? ":" type_expr
return_type: ":" type_expr

index_sig: "[" IDENT ":" ("string" | "number") "]" ":" type_expr ";"?

type_expr: basic_type
         | union_type
         | generic_type
         | function_type
         | object_type
         | array_type

basic_type: "string" | "number" | "boolean" | "any" | "void" | "never" | "unknown" | IDENT
union_type: type_expr ("|" type_expr)+
generic_type: IDENT "<" type_args ">"
type_args: type_expr ("," type_expr)*
function_type: "(" function_params? ")" "=>" type_expr
function_params: function_param ("," function_param)*
function_param: IDENT ":" type_expr
object_type: "{" object_type_members? "}"
object_type_members: object_type_member ("," object_type_member)* ","?
object_type_member: IDENT optional_marker? ":" type_expr
array_type: type_expr "[" "]"

IDENT: /[a-zA-Z_$][a-zA-Z0-9_$]*/

%ignore /\s+/
%ignore /\/\/.*/
%ignore /\/\*[\s\S]*?\*\//
""",
)

# Type alias grammar
TYPESCRIPT_TYPE_ALIAS = GrammarTemplate(
    name="typescript_type_alias",
    language="typescript",
    description="Grammar for TypeScript type alias declarations",
    grammar="""
start: type_alias

type_alias: export_modifier? "type" IDENT type_params? "=" type_expr ";"?

export_modifier: "export"

type_params: "<" type_param ("," type_param)* ">"
type_param: IDENT type_constraint?
type_constraint: "extends" type_expr

type_expr: basic_type
         | union_type
         | intersection_type
         | generic_type
         | function_type
         | object_type
         | array_type
         | tuple_type
         | literal_type

basic_type: "string" | "number" | "boolean" | "any" | "void" | "never" | "unknown" | IDENT
union_type: type_expr ("|" type_expr)+
intersection_type: type_expr ("&" type_expr)+
generic_type: IDENT "<" type_args ">"
type_args: type_expr ("," type_expr)*
function_type: "(" function_params? ")" "=>" type_expr
function_params: function_param ("," function_param)*
function_param: IDENT ":" type_expr
object_type: "{" object_type_members? "}"
object_type_members: object_type_member (";" object_type_member)* ";"?
object_type_member: IDENT optional_marker? ":" type_expr
optional_marker: "?"
array_type: type_expr "[" "]"
tuple_type: "[" tuple_elements "]"
tuple_elements: type_expr ("," type_expr)*
literal_type: STRING | NUMBER | BOOLEAN

IDENT: /[a-zA-Z_$][a-zA-Z0-9_$]*/
NUMBER: /-?\\d+(\\.\\d+)?/
STRING: /"([^"\\\\]|\\\\.)*"/ | /'([^'\\\\]|\\\\.)*'/
BOOLEAN: "true" | "false"

%ignore /\\s+/
%ignore /\\/\\/.*/
%ignore /\\/\\*[\\s\\S]*?\\*\\//
""",
)

# File-level grammar (for complete files)
TYPESCRIPT_FILE = GrammarTemplate(
    name="typescript_file",
    language="typescript",
    description="Grammar for complete TypeScript files",
    grammar="""
start: file

file: (import_stmt | export_stmt | declaration)*

import_stmt: "import" import_clause "from" module_specifier ";"
import_clause: named_imports | namespace_import | default_import
named_imports: "{" import_specifier ("," import_specifier)* "}"
import_specifier: IDENT ("as" IDENT)?
namespace_import: "*" "as" IDENT
default_import: IDENT

export_stmt: "export" (declaration | export_clause)
export_clause: "{" export_specifier ("," export_specifier)* "}"
export_specifier: IDENT ("as" IDENT)?

declaration: interface_decl
           | type_alias
           | function_decl
           | class_decl
           | var_decl

interface_decl: "interface" IDENT "{" interface_members? "}"
interface_members: (IDENT ":" type_expr ";")*

type_alias: "type" IDENT "=" type_expr ";"

function_decl: "function" IDENT "(" params? ")" return_type? block
params: param ("," param)*
param: IDENT ":" type_expr
return_type: ":" type_expr
block: "{" /[^}]*/ "}"

class_decl: "class" IDENT "{" class_members? "}"
class_members: (IDENT ":" type_expr ";")*

var_decl: ("const" | "let") IDENT ":" type_expr "=" expression ";"
expression: /.+/

type_expr: IDENT | basic_type
basic_type: "string" | "number" | "boolean" | "any" | "void"

module_specifier: STRING

IDENT: /[a-zA-Z_$][a-zA-Z0-9_$]*/
STRING: /"([^"\\\\]|\\\\.)*"/ | /'([^'\\\\]|\\\\.)*'/

%ignore /\\s+/
%ignore /\\/\\/.*/
%ignore /\\/\\*[\\s\\S]*?\\*\\//
""",
)

# Function BODY grammar (for completing partial signatures)
TYPESCRIPT_FUNCTION_BODY = GrammarTemplate(
    name="typescript_function_body",
    language="typescript",
    description="Grammar for TypeScript function body (completion after signature)",
    grammar="""
start: block

block: "{" statement* "}"

statement: return_stmt
         | var_decl
         | expr_stmt
         | if_stmt
         | for_stmt
         | while_stmt

return_stmt: "return" expression? ";"
var_decl: const_var | let_var
const_var: "const" IDENT type_annotation? "=" expression ";"
let_var: "let" IDENT type_annotation? ("=" expression)? ";"
type_annotation: ":" type_expr
expr_stmt: expression ";"

if_stmt: "if" "(" expression ")" block ("else" block)?
for_stmt: "for" "(" for_init? ";" expression? ";" expression? ")" block
for_init: var_decl | expression
while_stmt: "while" "(" expression ")" block

expression: literal
          | IDENT
          | call_expr
          | member_expr
          | binary_expr
          | unary_expr
          | paren_expr
          | template_literal
          | object_literal
          | array_literal
          | arrow_function

call_expr: expression "(" args? ")"
args: expression ("," expression)*

member_expr: expression "." IDENT
           | expression "[" expression "]"

binary_expr: expression binary_op expression
binary_op: "+" | "-" | "*" | "/" | "%" | "===" | "!==" | "==" | "!=" | "<" | ">" | "<=" | ">=" | "&&" | "||" | "??" | "&" | "|"

unary_expr: unary_op expression
unary_op: "!" | "-" | "+" | "typeof" | "void" | "await"

paren_expr: "(" expression ")"

template_literal: "`" template_part* "`"
template_part: /[^`$]+/ | "${" expression "}"

object_literal: "{" object_props? "}"
object_props: object_prop ("," object_prop)* ","?
object_prop: IDENT ":" expression
           | IDENT

array_literal: "[" array_elements? "]"
array_elements: expression ("," expression)* ","?

arrow_function: arrow_params "=>" (block | expression)
arrow_params: IDENT | "(" params? ")"
params: param ("," param)*
param: IDENT ":" type_expr

literal: NUMBER | STRING | BOOLEAN | NULL | UNDEFINED

type_expr: basic_type
         | union_type
         | generic_type
         | function_type
         | object_type
         | array_type

basic_type: "string" | "number" | "boolean" | "any" | "void" | "never" | "unknown" | IDENT
union_type: type_expr ("|" type_expr)+
generic_type: IDENT "<" type_args ">"
type_args: type_expr ("," type_expr)*
function_type: "(" function_params? ")" "=>" type_expr
function_params: function_param ("," function_param)*
function_param: IDENT ":" type_expr
object_type: "{" object_type_members? "}"
object_type_members: object_type_member ("," object_type_member)* ","?
object_type_member: IDENT optional_marker? ":" type_expr
optional_marker: "?"
array_type: type_expr "[" "]"

IDENT: /[a-zA-Z_$][a-zA-Z0-9_$]*/
NUMBER: /-?\\d+(\\.\\d+)?([eE][+-]?\\d+)?/
STRING: /"([^"\\\\]|\\\\.)*"/ | /'([^'\\\\]|\\\\.)*'/
BOOLEAN: "true" | "false"
NULL: "null"
UNDEFINED: "undefined"

%ignore /\\s+/
%ignore /\\/\\/.*/
%ignore /\\/\\*[\\s\\S]*?\\*\\//
""",
)

# Export all templates
ALL_TEMPLATES = [
    TYPESCRIPT_FUNCTION,
    TYPESCRIPT_FUNCTION_BODY,
    TYPESCRIPT_INTERFACE,
    TYPESCRIPT_TYPE_ALIAS,
    TYPESCRIPT_FILE,
]

__all__ = [
    "TYPESCRIPT_FUNCTION",
    "TYPESCRIPT_FUNCTION_BODY",
    "TYPESCRIPT_INTERFACE",
    "TYPESCRIPT_TYPE_ALIAS",
    "TYPESCRIPT_FILE",
    "ALL_TEMPLATES",
]
