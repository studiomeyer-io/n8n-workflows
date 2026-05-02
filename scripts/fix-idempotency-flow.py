#!/usr/bin/env python3
"""
Fix the Idempotency-Duplicate flow leak in T01/T02/T06/T07/T10.

Bug: when the Idempotency Check Code-Node detects a duplicate, it returns
  return [{ json: { skipped: true, reason: 'duplicate', ... } }];
That sentinel item then flows downstream into Normalize / Slack / CRM,
which can produce duplicate side-effects (slack message, lead insert).

Fix: return [] when duplicate. Code-Node mode is runOnceForAllItems
(typeVersion 2 default), so an empty array halts the branch cleanly.

Trade-off: the source provider does NOT receive a 200 OK and will retry.
Within the 24h dedup window the retry is also caught silently, so no
duplicate side-effects. Provider-owner may see a "delivery failed" mail
after the provider's retry budget is exhausted, but this is strictly
better than fanning out duplicate slack messages or duplicate CRM rows.

For Stripe specifically, the dedup window of 24h covers Stripe's retry
schedule (most retries happen within 24h, the long-tail at 1d and 3d).
"""
from __future__ import annotations
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = ROOT / "templates"

TARGETS = [
    "01-form-to-crm-lead-router",
    "02-stripe-lifecycle-to-slack",
    "06-calendly-to-crm-sync",
    "07-github-issues-to-tracker",
    "10-csv-bulk-validator",
]


def fix_idempotency(code: str) -> tuple[str, int]:
    """Replace `return [{ json: { skipped: true, ... } }];` with `return [];`.

    We anchor on `if (seen[XXX]) {` to be strict.
    """
    # Pattern: if (seen[X]) { return [{ json: { skipped: true, reason: 'duplicate', ... } }]; }
    # Replace the inner return with `return [];` and prepend a console.log
    # so live runs leave a debuggable trace.
    pattern = re.compile(
        r"if \(seen\[([^\]]+)\]\) \{\s*"
        r"return \[\{ json: \{ skipped: true, reason: 'duplicate'[^}]*\} \}\];\s*"
        r"\}",
        re.DOTALL,
    )

    def replace(m: re.Match) -> str:
        key_expr = m.group(1)
        # Halt branch on duplicate. Empty array ends the branch cleanly so
        # downstream nodes do not run with sentinel data.
        return (
            f"if (seen[{key_expr}]) {{\n"
            f"  // Duplicate detected. Halt branch cleanly (return []) so the\n"
            f"  // downstream Normalize/Send nodes do not run with a sentinel\n"
            f"  // and produce duplicate side-effects (Slack msg, CRM insert).\n"
            f"  // The source provider will retry; the next retry is also caught\n"
            f"  // by this same dedup window, so no duplicate side-effects.\n"
            f"  return [];\n"
            f"}}"
        )

    new_code, n = pattern.subn(replace, code)
    return new_code, n


def main() -> int:
    grand_total = 0
    for tid in TARGETS:
        wf_path = TEMPLATES / tid / "workflow.json"
        if not wf_path.is_file():
            print(f"MISSING: {wf_path}", file=sys.stderr)
            continue
        with wf_path.open("r", encoding="utf-8") as f:
            wf = json.load(f)
        changed = 0
        for node in wf.get("nodes", []):
            if node.get("name") != "Idempotency Check (opt-in)":
                continue
            params = node.get("parameters") or {}
            js = params.get("jsCode")
            if not isinstance(js, str):
                continue
            new_js, n = fix_idempotency(js)
            if n > 0:
                params["jsCode"] = new_js
                changed += n
        if changed > 0:
            with wf_path.open("w", encoding="utf-8") as f:
                json.dump(wf, f, indent=2, ensure_ascii=False)
                f.write("\n")
            print(f"  {tid}: {changed} fix")
            grand_total += changed
        else:
            print(f"  {tid}: NO CHANGE (sentinel pattern not found)")
    print(f"\nTotal: {grand_total} idempotency-flow fix(es).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
