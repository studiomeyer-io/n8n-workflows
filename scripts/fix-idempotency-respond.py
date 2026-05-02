#!/usr/bin/env python3
"""
HIGH-finding from S965 Critic-Review: T02 Stripe + T01/T06/T07/T10 all use
`responseMode: responseNode` on their Webhook trigger. Our Bug 2 fix
(`return []` on duplicate) halts the branch BUT no `respondToWebhook`
node runs, so n8n holds the HTTP connection open until Stripe's 30s
timeout. Stripe marks delivery "failed" and retries every few hours
for 3 days. Same problem for Calendly (24h retries), GitHub (24h),
form providers, CSV uploaders.

Correct pattern: route duplicates through a dedicated `Respond Duplicate`
node via an `IF` gateway. Live items go through the existing chain.

This script:
  1. Reverts the Idempotency Check Code-Node to emit a sentinel item
     `[{ json: { skipped: true, reason: 'duplicate', ...keyMeta } }]`
     when a duplicate is detected.
  2. Inserts an `IF` node `Skip If Duplicate` between
     `Idempotency Check (opt-in)` and the existing downstream node.
     - true (skipped)  -> Respond Duplicate (new)
     - false (live)    -> existing downstream node
  3. Inserts a `respondToWebhook` node `Respond Duplicate` that returns
     200 + `{ ok: true, deduped: true, reason: 'duplicate' }`.
  4. Rewires connections accordingly.

Idempotent: re-running detects the IF node and skips.
"""
from __future__ import annotations
import copy
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

IDEMPOTENCY_NODE_NAME = "Idempotency Check (opt-in)"
IF_NODE_NAME = "Skip If Duplicate"
RESPOND_NODE_NAME = "Respond Duplicate"


def revert_idempotency_to_sentinel(code: str) -> tuple[str, int]:
    """Replace the `return [];` halt with a sentinel-emit pattern."""
    pattern = re.compile(
        r"if \(seen\[([^\]]+)\]\) \{[^}]*?return \[\];[^}]*?\}",
        re.DOTALL,
    )

    def replace(m: re.Match) -> str:
        key_expr = m.group(1)
        return (
            f"if (seen[{key_expr}]) {{\n"
            f"  // Duplicate detected. Emit a sentinel item that the\n"
            f"  // 'Skip If Duplicate' IF node routes to 'Respond Duplicate'\n"
            f"  // (200 OK + {{ deduped: true }}). Without that 200 the source\n"
            f"  // provider would hold the HTTP connection until n8n's webhook\n"
            f"  // timeout (default 30s) and mark delivery failed.\n"
            f"  return [{{ json: {{ skipped: true, reason: 'duplicate', dedupKey: String({key_expr}) }} }}];\n"
            f"}}"
        )

    new_code, n = pattern.subn(replace, code)
    return new_code, n


def main() -> int:
    grand = 0
    for tid in TARGETS:
        wf_path = TEMPLATES / tid / "workflow.json"
        if not wf_path.is_file():
            print(f"MISSING {wf_path}", file=sys.stderr)
            continue

        with wf_path.open("r", encoding="utf-8") as f:
            wf = json.load(f)

        nodes = wf.get("nodes", [])
        node_names = {n["name"] for n in nodes}

        # Idempotent re-run guard
        if IF_NODE_NAME in node_names and RESPOND_NODE_NAME in node_names:
            print(f"  {tid}: already has IF + Respond Duplicate, skipping")
            continue

        # 1) Find the Idempotency Check node and revert its return value
        idem_node = next(
            (n for n in nodes if n.get("name") == IDEMPOTENCY_NODE_NAME), None
        )
        if idem_node is None:
            print(f"  {tid}: NO Idempotency Check node, skipping", file=sys.stderr)
            continue

        params = idem_node.get("parameters") or {}
        js = params.get("jsCode", "")
        new_js, n_revert = revert_idempotency_to_sentinel(js)
        if n_revert == 0:
            print(
                f"  {tid}: WARN, could not revert idempotency Code-Node "
                f"(return [] pattern not found, may already be sentinel)"
            )
        else:
            params["jsCode"] = new_js

        # 2) Find the connection: Idempotency Check (opt-in) -> <downstream>
        connections = wf.setdefault("connections", {})
        idem_out = connections.get(IDEMPOTENCY_NODE_NAME, {}).get("main", [])
        if not idem_out or not idem_out[0]:
            print(
                f"  {tid}: WARN, Idempotency Check has no downstream, skipping",
                file=sys.stderr,
            )
            continue
        downstream_node = idem_out[0][0]["node"]
        downstream_index = idem_out[0][0].get("index", 0)
        downstream_type = idem_out[0][0].get("type", "main")

        # 3) Compute IF + Respond positions next to Idempotency Check
        idem_pos = idem_node.get("position", [800, 0])
        if_pos = [idem_pos[0] + 220, idem_pos[1]]
        respond_pos = [idem_pos[0] + 440, idem_pos[1] - 180]

        # 4) Build the IF node (typeVersion 2)
        if_node = {
            "parameters": {
                "conditions": {
                    "options": {
                        "caseSensitive": True,
                        "leftValue": "",
                        "typeValidation": "strict",
                        "version": 2,
                    },
                    "conditions": [
                        {
                            "id": f"cond-{tid}-skipped",
                            "leftValue": "={{ $json.skipped }}",
                            "rightValue": True,
                            "operator": {
                                "type": "boolean",
                                "operation": "true",
                                "singleValue": True,
                            },
                        }
                    ],
                    "combinator": "and",
                },
                "options": {},
            },
            "id": f"{tid[:6]}-if-skip-dup",
            "name": IF_NODE_NAME,
            "type": "n8n-nodes-base.if",
            "typeVersion": 2,
            "position": if_pos,
        }

        # 5) Build the Respond Duplicate node
        respond_node = {
            "parameters": {
                "respondWith": "json",
                "responseBody": '={{ JSON.stringify({ ok: true, deduped: true, reason: "duplicate" }) }}',
                "options": {
                    "responseCode": 200,
                    "responseHeaders": {
                        "entries": [
                            {"name": "X-Dedup", "value": "1"}
                        ]
                    },
                },
            },
            "id": f"{tid[:6]}-respond-duplicate",
            "name": RESPOND_NODE_NAME,
            "type": "n8n-nodes-base.respondToWebhook",
            "typeVersion": 1.1,
            "position": respond_pos,
        }

        nodes.append(if_node)
        nodes.append(respond_node)

        # 6) Rewire connections:
        #   Idempotency Check (opt-in) -> Skip If Duplicate (REPLACE)
        #   Skip If Duplicate [true]  -> Respond Duplicate
        #   Skip If Duplicate [false] -> <existing downstream>
        connections[IDEMPOTENCY_NODE_NAME] = {
            "main": [
                [
                    {
                        "node": IF_NODE_NAME,
                        "type": "main",
                        "index": 0,
                    }
                ]
            ]
        }
        connections[IF_NODE_NAME] = {
            "main": [
                [  # Output 0 = true (skipped)
                    {
                        "node": RESPOND_NODE_NAME,
                        "type": "main",
                        "index": 0,
                    }
                ],
                [  # Output 1 = false (live)
                    {
                        "node": downstream_node,
                        "type": downstream_type,
                        "index": downstream_index,
                    }
                ],
            ]
        }
        # Respond Duplicate is a terminal node, no outgoing connections.

        with wf_path.open("w", encoding="utf-8") as f:
            json.dump(wf, f, indent=2, ensure_ascii=False)
            f.write("\n")
        print(
            f"  {tid}: revert={n_revert} fix, +IF '{IF_NODE_NAME}', "
            f"+Respond '{RESPOND_NODE_NAME}', rewired -> {downstream_node!r}"
        )
        grand += 1

    print(f"\nTotal templates patched: {grand}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
