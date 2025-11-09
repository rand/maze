# Constraint strategies and grammar snippets

## JSON Schema → Lark with `%json`
LLGuidance allows embedding JSON Schema in an extended Lark grammar:
```
start: <think> "\n" /(.|\n)*/ </think> result
result: %json { "type":"object",
  "properties":{
    "file": {"type":"string"},
    "diff": {"type":"string"}
  },
  "required":["file","diff"],
  "additionalProperties": false
}
%ignore /[ \t\r\n]+/
```

## Code skeleton grammar (TypeScript)
```
?start: file
file: import_stmt* stmt*
import_stmt: "import" /[A-Za-z0-9_,{}\s\*]+/ "from" "'" /[^']+/ "'" ";"
stmt: func_decl | class_decl | export_decl | other_stmt
func_decl: "export"?"function" IDENT "(" params? ")" ret? "{" block "}"

IDENT: /[A-Za-z_\$][A-Za-z0-9_\$]*/
ret: ":" TYPE
params: param ("," param)*
param: IDENT ":" TYPE
TYPE: /[A-Za-z0-9_\[\]\<\>\|\&\.\?\:\{\}]+/
block: /(.|\n)*/

%ignore /[ \t\r\n]+/
```

## Style constraints (regex)
- camelCase identifiers: `/^[a-z][A-Za-z0-9]*$/`
- quote style enforcement in grammar tokens.

## Typed‑hole stub markup
Emit literal markers the compiler understands, then fill under stricter grammar:
```ts
// HOLE(name: formatAddress, type: (u: User) => string)
export function formatAddress(u: User): string {
  /*__HOLE_formatAddress__*/
}
```

## JSON edit plan schema (for tool calls)
```json
{
  "type":"object",
  "properties": {
    "file": {"type":"string"},
    "edits": {
      "type":"array",
      "items": {
        "type":"object",
        "properties": {
          "range": {"type":"object","properties":{
            "start":{"type":"integer"},"end":{"type":"integer"}
          },"required":["start","end"]},
          "text": {"type":"string"}
        },
        "required": ["range","text"]
      }
    }
  },
  "required": ["file","edits"],
  "additionalProperties": false
}
```
