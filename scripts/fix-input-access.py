#!/usr/bin/env python3
"""
Fix the $input.first() input-access bug across all n8n workflow.json files.

n8n's $input.first() returns INodeExecutionData with shape:
  { json: {...}, binary?: {...}, paired?: {...} }

For Webhook-trigger downstream code-nodes, the payload lives at
$input.first().json.body / .json.headers / .json.rawBody

The bug: several templates wrote $input.first().body etc., which
returns undefined and silently gets `|| {}`'d. Result: workflow runs
with empty body and corrupts everything downstream.

Fixes:
  $input.first().body         -> $input.first().json.body
  $input.first().headers      -> $input.first().json.headers
  $input.first().rawBody      -> $input.first().json.rawBody
  $input.first().params       -> $input.first().json.params
  $input.first().query        -> $input.first().json.query

Plus the destructured pattern:
  const item = $input.first();
  item.body / item.headers / item.rawBody / item.params / item.query
  ->
  item.json.body / item.json.headers / item.json.rawBody / item.json.params / item.json.query

We are conservative: we only rewrite `item.X` when the preceding line
(within the same code-node) literally contains `$input.first()`.
"""
from __future__ import annotations
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = ROOT / "templates"

# Direct call patterns: $input.first().body -> $input.first().json.body
DIRECT_PATTERNS = [
    (re.compile(r"\$input\.first\(\)\.(body|headers|rawBody|params|query)\b"),
     r"$input.first().json.\1"),
]

# Destructured: const X = $input.first(); ... X.body -> X.json.body
# We detect any local var bound to $input.first() and rewrite its accesses.
ASSIGN_RE = re.compile(
    r"(?:const|let|var)\s+(\w+)\s*=\s*\$input\.first\(\)\s*;"
)

# ES6 object destructure: const { body, headers } = $input.first();
# This is also wrong. Destructuring lifts top-level keys off the
# INodeExecutionData wrapper (which only carries { json, binary, paired }),
# so body and headers are always undefined. Fix: rewrite the RHS to
# $input.first().json so the destructured keys come from the payload.
# Negative lookahead `(?!\.json)` keeps the rule idempotent.
DESTRUCTURE_RE = re.compile(
    r"((?:const|let|var)\s*\{[^}]+\}\s*=\s*\$input\.first\(\))(?!\.json)"
)

# Other $input forms that have the same wrapper-shape problem:
#   $input.last().body   -> $input.last().json.body
#   $input.all()[0].body -> $input.all()[0].json.body
#   $input.first()['body'] -> $input.first().json['body'] (bracket notation)
LAST_RE = re.compile(
    r"\$input\.last\(\)\.(body|headers|rawBody|params|query)\b"
)
ALL_INDEX_RE = re.compile(
    r"\$input\.all\(\)\[(\d+)\]\.(body|headers|rawBody|params|query)\b"
)
FIRST_BRACKET_RE = re.compile(
    r"\$input\.first\(\)\[(['\"])(body|headers|rawBody|params|query)\1\]"
)


def fix_jscode(code: str) -> tuple[str, int]:
    """Return (fixed_code, n_changes)."""
    changes = 0

    # Pass 1: direct $input.first().X
    def direct_sub(m: re.Match) -> str:
        nonlocal changes
        changes += 1
        return f"$input.first().json.{m.group(1)}"

    code = DIRECT_PATTERNS[0][0].sub(direct_sub, code)

    # Pass 1b: bracket notation $input.first()['body']
    def bracket_sub(m: re.Match) -> str:
        nonlocal changes
        changes += 1
        quote = m.group(1)
        key = m.group(2)
        return f"$input.first().json[{quote}{key}{quote}]"

    code = FIRST_BRACKET_RE.sub(bracket_sub, code)

    # Pass 1c: $input.last().X (rare, but same wrapper shape)
    def last_sub(m: re.Match) -> str:
        nonlocal changes
        changes += 1
        return f"$input.last().json.{m.group(1)}"

    code = LAST_RE.sub(last_sub, code)

    # Pass 1d: $input.all()[N].X
    def all_index_sub(m: re.Match) -> str:
        nonlocal changes
        changes += 1
        return f"$input.all()[{m.group(1)}].json.{m.group(2)}"

    code = ALL_INDEX_RE.sub(all_index_sub, code)

    # Pass 2: ES6 destructure on $input.first()
    def destruct_sub(m: re.Match) -> str:
        nonlocal changes
        changes += 1
        return f"{m.group(1)}.json"

    code = DESTRUCTURE_RE.sub(destruct_sub, code)

    # Pass 3: destructured var assigned to $input.first()
    # Find ALL `const X = $input.first();` assignments in this code.
    aliases = {m.group(1) for m in ASSIGN_RE.finditer(code)}
    for alias in aliases:
        # Rewrite ALIAS.body / ALIAS.headers etc., but ONLY when ALIAS
        # references $input.first() (top-level wrapper, not .json sub-object).
        access_re = re.compile(
            rf"\b{re.escape(alias)}\.(body|headers|rawBody|params|query)\b"
        )

        def alias_sub(m: re.Match) -> str:
            nonlocal changes
            changes += 1
            return f"{alias}.json.{m.group(1)}"

        code = access_re.sub(alias_sub, code)

    return code, changes


def fix_workflow(path: Path) -> int:
    with path.open("r", encoding="utf-8") as f:
        wf = json.load(f)

    total = 0
    for node in wf.get("nodes", []):
        params = node.get("parameters") or {}
        js = params.get("jsCode")
        if not isinstance(js, str):
            continue
        new_js, n = fix_jscode(js)
        if n > 0:
            params["jsCode"] = new_js
            total += n
            print(f"  {path.name}::{node['name']!r}: {n} fix(es)")

    if total > 0:
        with path.open("w", encoding="utf-8") as f:
            json.dump(wf, f, indent=2, ensure_ascii=False)
            f.write("\n")
    return total


def main() -> int:
    if not TEMPLATES.is_dir():
        print(f"templates/ not found at {TEMPLATES}", file=sys.stderr)
        return 1

    grand_total = 0
    files_changed = 0
    for d in sorted(TEMPLATES.iterdir()):
        wf_file = d / "workflow.json"
        if not wf_file.is_file():
            continue
        print(f"Scanning {d.name}/workflow.json")
        n = fix_workflow(wf_file)
        if n > 0:
            files_changed += 1
            grand_total += n

    print()
    print(f"Total: {grand_total} fix(es) across {files_changed} file(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
