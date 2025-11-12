"""
Rust grammar templates for constrained code generation.

Provides Lark grammar templates for common Rust constructs.
"""

from maze.synthesis.grammar_builder import GrammarTemplate

# Basic Rust function grammar
RUST_FUNCTION = GrammarTemplate(
    name="rust_function",
    language="rust",
    description="Grammar for Rust function definitions",
    grammar="""
start: function_def

function_def: attributes? visibility? qualifiers? "fn" IDENT generics? "(" parameters? ")" return_type? where_clause? block

attributes: attribute+
attribute: "#" "[" attribute_content "]"
attribute_content: /[^\\]]+/

visibility: "pub" visibility_restriction?
visibility_restriction: "(" ("crate" | "super" | "self" | "in" path) ")"

qualifiers: qualifier+
qualifier: "const" | "async" | "unsafe" | "extern" abi?
abi: STRING

generics: "<" generic_params ">"
generic_params: generic_param ("," generic_param)* ","?
generic_param: lifetime | type_param | const_param
lifetime: "'" IDENT
type_param: IDENT type_bound?
type_bound: ":" trait_bounds
trait_bounds: trait_bound ("+" trait_bound)*
trait_bound: lifetime | trait_path
trait_path: path
const_param: "const" IDENT ":" type_expr

parameters: param ("," param)* ","?
param: pattern ":" type_expr

pattern: IDENT
       | "_"
       | "&" "mut"? pattern
       | "mut" pattern

return_type: "->" type_expr

where_clause: "where" where_predicates
where_predicates: where_predicate ("," where_predicate)* ","?
where_predicate: lifetime ":" lifetime_bounds
               | type_expr ":" trait_bounds
lifetime_bounds: lifetime ("+" lifetime)*

block: "{" statement* expression? "}"

statement: let_stmt
         | expr_stmt

let_stmt: "let" "mut"? pattern type_annotation? ("=" expression)? ";"
type_annotation: ":" type_expr
expr_stmt: expression ";"

expression: literal
          | path
          | call
          | method_call
          | field_access
          | index
          | unary_expr
          | binary_expr
          | range
          | if_expr
          | match_expr
          | loop_expr
          | block_expr
          | return_expr
          | break_expr
          | continue_expr
          | macro_call
          | closure
          | tuple
          | array
          | struct_expr

path: "::"? path_segment ("::" path_segment)*
path_segment: IDENT generic_args?
generic_args: "<" generic_arg_list ">"
generic_arg_list: generic_arg ("," generic_arg)* ","?
generic_arg: type_expr | lifetime | literal

call: expression "(" call_args? ")"
call_args: expression ("," expression)* ","?

method_call: expression "." IDENT generic_args? "(" call_args? ")"

field_access: expression "." IDENT
            | expression "." NUMBER

index: expression "[" expression "]"

unary_expr: unary_op expression
unary_op: "-" | "!" | "*" | "&" "mut"? | "&" lifetime? "mut"?

binary_expr: expression binary_op expression
binary_op: "+" | "-" | "*" | "/" | "%" | "&&" | "||" | "&" | "|" | "^" | "<<" | ">>"
         | "==" | "!=" | "<" | ">" | "<=" | ">=" | "=" | "+=" | "-=" | "*=" | "/="

range: expression ".." expression?
     | expression "..=" expression
     | ".." expression?
     | "..=" expression

if_expr: "if" expression block ("else" (block | if_expr))?

match_expr: "match" expression "{" match_arms? "}"
match_arms: match_arm ("," match_arm)* ","?
match_arm: pattern match_guard? "=>" (expression | block)
match_guard: "if" expression

loop_expr: "loop" block
         | "while" expression block
         | "for" pattern "in" expression block

block_expr: block

return_expr: "return" expression?
break_expr: "break" expression?
continue_expr: "continue"

macro_call: path "!" macro_args
macro_args: "(" macro_tokens ")" | "[" macro_tokens "]" | "{" macro_tokens "}"
macro_tokens: /[^)\\]\\}]*/

closure: "|" closure_params? "|" (return_type)? (expression | block)
closure_params: closure_param ("," closure_param)*
closure_param: pattern type_annotation?

tuple: "(" tuple_elements? ")"
tuple_elements: expression ("," expression)+ ","?
              | expression ","

array: "[" array_elements "]"
array_elements: expression ("," expression)* ","?
              | expression ";" expression

struct_expr: path "{" struct_fields? "}"
struct_fields: struct_field ("," struct_field)* ","?
struct_field: IDENT ":" expression | IDENT

literal: NUMBER | STRING | CHAR | BOOLEAN
NUMBER: /-?\\d+(_?\\d)*(\\.\\d+(_?\\d)*)?([eE][+-]?\\d+)?/ | /-?0[xX][0-9a-fA-F]+(_?[0-9a-fA-F])*/ | /-?0[oO][0-7]+(_?[0-7])*/ | /-?0[bB][01]+(_?[01])*/
STRING: /"([^"\\\\]|\\\\.)*"/ | /r(#*)".*?"\\1/
CHAR: /'([^'\\\\]|\\\\.)'/
BOOLEAN: "true" | "false"

type_expr: primitive_type
         | path_type
         | reference_type
         | pointer_type
         | array_type
         | tuple_type
         | fn_type
         | trait_object

primitive_type: "i8" | "i16" | "i32" | "i64" | "i128" | "isize"
              | "u8" | "u16" | "u32" | "u64" | "u128" | "usize"
              | "f32" | "f64"
              | "bool" | "char" | "str" | "()"

path_type: path

reference_type: "&" lifetime? "mut"? type_expr

pointer_type: "*" ("const" | "mut") type_expr

array_type: "[" type_expr ";" expression "]"
          | "[" type_expr "]"

tuple_type: "(" tuple_type_elements ")"
tuple_type_elements: type_expr ("," type_expr)+ ","?

fn_type: "fn" "(" fn_params? ")" return_type?
fn_params: type_expr ("," type_expr)* ","?

trait_object: "dyn" trait_bounds

IDENT: /[a-zA-Z_][a-zA-Z0-9_]*/

%ignore /[ \\t\\r\\n]+/
%ignore /\\/\\/.*/
%ignore /\\/\\*[\\s\\S]*?\\*\\//
""",
)

# Struct definition grammar
RUST_STRUCT = GrammarTemplate(
    name="rust_struct",
    language="rust",
    description="Grammar for Rust struct definitions",
    grammar="""
start: struct_def

struct_def: attributes? visibility? "struct" IDENT generics? struct_body where_clause? ";"?

attributes: attribute+
attribute: "#" "[" attribute_content "]"
attribute_content: /[^\\]]+/

visibility: "pub" visibility_restriction?
visibility_restriction: "(" ("crate" | "super" | "self") ")"

generics: "<" generic_params ">"
generic_params: generic_param ("," generic_param)* ","?
generic_param: lifetime | type_param
lifetime: "'" IDENT
type_param: IDENT type_bound?
type_bound: ":" trait_bounds
trait_bounds: trait_bound ("+" trait_bound)*
trait_bound: path

struct_body: unit_struct | tuple_struct | named_struct

unit_struct: ""

tuple_struct: "(" tuple_fields? ")"
tuple_fields: tuple_field ("," tuple_field)* ","?
tuple_field: visibility? type_expr

named_struct: "{" named_fields? "}"
named_fields: named_field ("," named_field)* ","?
named_field: attributes? visibility? IDENT ":" type_expr

where_clause: "where" where_predicates
where_predicates: where_predicate ("," where_predicate)* ","?
where_predicate: lifetime ":" lifetime_bounds
               | type_expr ":" trait_bounds
lifetime_bounds: lifetime ("+" lifetime)*

path: "::"? path_segment ("::" path_segment)*
path_segment: IDENT

type_expr: primitive_type | path | reference_type | array_type | tuple_type

primitive_type: "i32" | "u32" | "i64" | "u64" | "f32" | "f64" | "bool" | "char" | "str"
reference_type: "&" lifetime? "mut"? type_expr
array_type: "[" type_expr ";" NUMBER "]"
tuple_type: "(" type_list ")"
type_list: type_expr ("," type_expr)* ","?

IDENT: /[a-zA-Z_][a-zA-Z0-9_]*/
NUMBER: /\\d+/

%ignore /[ \\t\\r\\n]+/
%ignore /\\/\\/.*/
%ignore /\\/\\*[\\s\\S]*?\\*\\//
""",
)

# Impl block grammar
RUST_IMPL = GrammarTemplate(
    name="rust_impl",
    language="rust",
    description="Grammar for Rust impl blocks",
    grammar="""
start: impl_block

impl_block: "impl" generics? trait_path? "for"? type_expr where_clause? "{" impl_items? "}"

generics: "<" generic_params ">"
generic_params: generic_param ("," generic_param)* ","?
generic_param: lifetime | type_param
lifetime: "'" IDENT
type_param: IDENT

trait_path: path

where_clause: "where" where_predicates
where_predicates: where_predicate ("," where_predicate)* ","?
where_predicate: type_expr ":" trait_bounds
trait_bounds: path ("+" path)*

impl_items: impl_item+
impl_item: function_def | type_alias | const_def

function_def: visibility? "fn" IDENT "(" parameters? ")" return_type? block
visibility: "pub"
parameters: param ("," param)* ","?
param: IDENT ":" type_expr
return_type: "->" type_expr
block: "{" /[^}]*/ "}"

type_alias: "type" IDENT "=" type_expr ";"

const_def: "const" IDENT ":" type_expr "=" expression ";"

path: IDENT ("::" IDENT)*
type_expr: IDENT | reference_type
reference_type: "&" "mut"? type_expr
expression: /[^;]+/

IDENT: /[a-zA-Z_][a-zA-Z0-9_]*/

%ignore /[ \\t\\r\\n]+/
%ignore /\\/\\/.*/
""",
)

# Function BODY grammar (for completing partial signatures)
RUST_FUNCTION_BODY = GrammarTemplate(
    name="rust_function_body",
    language="rust",
    description="Grammar for Rust function body (completion after signature)",
    grammar="""
start: block

block: "{" statement* expression? "}"

statement: let_stmt
         | expr_stmt

let_stmt: "let" "mut"? pattern type_annotation? ("=" expression)? ";"
type_annotation: ":" type_expr
expr_stmt: expression ";"

pattern: IDENT
       | "_"
       | "&" "mut"? pattern
       | "mut" pattern

expression: literal
          | path
          | call
          | method_call
          | field_access
          | index
          | unary_expr
          | binary_expr
          | range
          | if_expr
          | match_expr
          | loop_expr
          | block_expr
          | return_expr
          | break_expr
          | continue_expr
          | macro_call
          | closure
          | tuple
          | array
          | struct_expr

path: "::"? path_segment ("::" path_segment)*
path_segment: IDENT generic_args?
generic_args: "<" generic_arg_list ">"
generic_arg_list: generic_arg ("," generic_arg)* ","?
generic_arg: type_expr | lifetime | literal
lifetime: "'" IDENT

call: expression "(" call_args? ")"
call_args: expression ("," expression)* ","?

method_call: expression "." IDENT generic_args? "(" call_args? ")"

field_access: expression "." IDENT
            | expression "." NUMBER

index: expression "[" expression "]"

unary_expr: unary_op expression
unary_op: "-" | "!" | "*" | "&" "mut"? | "&" lifetime? "mut"?

binary_expr: expression binary_op expression
binary_op: "+" | "-" | "*" | "/" | "%" | "&&" | "||" | "&" | "|" | "^" | "<<" | ">>"
         | "==" | "!=" | "<" | ">" | "<=" | ">=" | "=" | "+=" | "-=" | "*=" | "/="

range: expression ".." expression?
     | expression "..=" expression
     | ".." expression?
     | "..=" expression

if_expr: "if" expression block ("else" (block | if_expr))?

match_expr: "match" expression "{" match_arms? "}"
match_arms: match_arm ("," match_arm)* ","?
match_arm: pattern match_guard? "=>" (expression | block)
match_guard: "if" expression

loop_expr: "loop" block
         | "while" expression block
         | "for" pattern "in" expression block

block_expr: block

return_expr: "return" expression?
break_expr: "break" expression?
continue_expr: "continue"

macro_call: path "!" macro_args
macro_args: "(" macro_tokens ")" | "[" macro_tokens "]" | "{" macro_tokens "}"
macro_tokens: /[^)\\]\\}]*/

closure: "|" closure_params? "|" (return_type)? (expression | block)
closure_params: closure_param ("," closure_param)*
closure_param: pattern type_annotation?
return_type: "->" type_expr

tuple: "(" tuple_elements? ")"
tuple_elements: expression ("," expression)+ ","?
              | expression ","

array: "[" array_elements "]"
array_elements: expression ("," expression)* ","?
              | expression ";" expression

struct_expr: path "{" struct_fields? "}"
struct_fields: struct_field ("," struct_field)* ","?
struct_field: IDENT ":" expression | IDENT

literal: NUMBER | STRING | CHAR | BOOLEAN
NUMBER: /-?\\d+(_?\\d)*(\\.\\d+(_?\\d)*)?([eE][+-]?\\d+)?/ | /-?0[xX][0-9a-fA-F]+(_?[0-9a-fA-F])*/ | /-?0[oO][0-7]+(_?[0-7])*/ | /-?0[bB][01]+(_?[01])*/
STRING: /"([^"\\\\]|\\\\.)*"/ | /r(#*)".*?"\\1/
CHAR: /'([^'\\\\]|\\\\.)'/
BOOLEAN: "true" | "false"

type_expr: primitive_type
         | path_type
         | reference_type
         | pointer_type
         | array_type
         | tuple_type
         | fn_type
         | trait_object

primitive_type: "i8" | "i16" | "i32" | "i64" | "i128" | "isize"
              | "u8" | "u16" | "u32" | "u64" | "u128" | "usize"
              | "f32" | "f64"
              | "bool" | "char" | "str" | "()"

path_type: path

reference_type: "&" lifetime? "mut"? type_expr

pointer_type: "*" ("const" | "mut") type_expr

array_type: "[" type_expr ";" expression "]"
          | "[" type_expr "]"

tuple_type: "(" tuple_type_elements ")"
tuple_type_elements: type_expr ("," type_expr)+ ","?

fn_type: "fn" "(" fn_params? ")" return_type?
fn_params: type_expr ("," type_expr)* ","?

trait_object: "dyn" trait_bounds
trait_bounds: trait_bound ("+" trait_bound)*
trait_bound: path

IDENT: /[a-zA-Z_][a-zA-Z0-9_]*/

%ignore /[ \\t\\r\\n]+/
%ignore /\\/\\/.*/
%ignore /\\/\\*[\\s\\S]*?\\*\\//
""",
)

# Export all templates
ALL_TEMPLATES = [
    RUST_FUNCTION,
    RUST_FUNCTION_BODY,
    RUST_STRUCT,
    RUST_IMPL,
]

__all__ = [
    "RUST_FUNCTION",
    "RUST_FUNCTION_BODY",
    "RUST_STRUCT",
    "RUST_IMPL",
    "ALL_TEMPLATES",
]
