#!/usr/bin/env python3
"""
Fix T13 Webhook Audit-Trail Hash-Chain race condition.

Bug: the existing SQL relies on `SELECT row_hash FROM audit_log ORDER BY id
DESC LIMIT 1 FOR UPDATE` to read+lock the latest row. Two concurrent
inserts can both end up reading id=99 as the latest:

  Tx1: SELECT FOR UPDATE -> locks row 99 -> INSERT id=100 -> commit
  Tx2: SELECT FOR UPDATE -> blocks on row 99
  Tx2: lock released -> reads row 99 (its snapshot does NOT see Tx1's
       new id=100 because the CTE was already prepared) -> INSERT id=101
       with prev_hash = row_99.row_hash  -> COLLISION with id=100

This is a known PostgreSQL race for the "select latest with FOR UPDATE"
pattern.

Fix: serialize all inserts on a transaction-scoped advisory lock. The
lock is acquired in a MATERIALIZED CTE that is referenced via CROSS JOIN
by the `last` CTE, forcing PostgreSQL to evaluate the lock acquisition
before scanning audit_log. The lock is released when the implicit
transaction (per n8n Postgres v2.5 executeQuery) commits.

We keep the FOR UPDATE as a belt-and-suspenders defense against direct
SQL access bypassing this workflow.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WF_PATH = ROOT / "templates" / "13-webhook-audit-trail" / "workflow.json"

NEW_QUERY = """\
WITH advisory AS MATERIALIZED (
  -- Serialize all inserts on the same chain key. Transaction-scoped
  -- advisory lock is released on COMMIT/ROLLBACK. Using hashtext on a
  -- chain identifier so multiple chains (e.g. per-tenant) do not block
  -- each other if you ever need to shard.
  SELECT pg_advisory_xact_lock(hashtext('audit_log_chain:default')) AS lock_acquired
),
last AS MATERIALIZED (
  -- CROSS JOIN advisory forces PostgreSQL to evaluate the advisory CTE
  -- before scanning audit_log. With MATERIALIZED on advisory, the
  -- ordering is guaranteed even on PG 12+ where CTEs are inlined by
  -- default. FOR UPDATE stays as a belt-and-suspenders defense in case
  -- a direct SQL writer bypasses this workflow.
  SELECT row_hash AS prev_hash
  FROM audit_log
  CROSS JOIN advisory
  ORDER BY id DESC
  LIMIT 1
  FOR UPDATE
),
seed AS (
  SELECT
    COALESCE((SELECT prev_hash FROM last), repeat('0', 64)) AS prev_hash,
    $1::timestamptz AS received_at,
    $2::text AS event_type,
    $3::text AS event_source,
    NULLIF($4, '')::text AS source_ip,
    NULLIF($5, '')::text AS source_user_agent,
    $6::boolean AS signed,
    $7::text AS payload,
    $8::text AS payload_hash,
    NULLIF($9, '')::text AS dedup_key
)
INSERT INTO audit_log (received_at, event_type, event_source, source_ip, source_user_agent, signed, payload, payload_hash, prev_hash, row_hash, dedup_key)
SELECT
  received_at, event_type, event_source, source_ip, source_user_agent, signed, payload, payload_hash, prev_hash,
  encode(
    digest(
      json_build_object(
        'prevHash', prev_hash,
        'payloadHash', payload_hash,
        'signed', signed,
        'sourceIp', source_ip,
        'sourceUserAgent', source_user_agent,
        'eventType', event_type,
        'eventSource', event_source,
        'receivedAt', to_char(received_at AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.MSZ')
      )::text,
      'sha256'
    ),
    'hex'
  ) AS row_hash,
  dedup_key
FROM seed
RETURNING id, prev_hash, row_hash;\
"""


def main() -> int:
    if not WF_PATH.is_file():
        print(f"NOT FOUND: {WF_PATH}", file=sys.stderr)
        return 1

    with WF_PATH.open("r", encoding="utf-8") as f:
        wf = json.load(f)

    found = False
    for node in wf.get("nodes", []):
        if node.get("name") != "Postgres Insert":
            continue
        params = node.get("parameters") or {}
        old = params.get("query", "")
        if "pg_advisory_xact_lock" in old:
            print("ALREADY FIXED, pg_advisory_xact_lock present.")
            return 0
        params["query"] = NEW_QUERY
        found = True
        print("OK: Postgres Insert query rewritten with advisory lock.")

    if not found:
        print("Did not find 'Postgres Insert' node.", file=sys.stderr)
        return 1

    with WF_PATH.open("w", encoding="utf-8") as f:
        json.dump(wf, f, indent=2, ensure_ascii=False)
        f.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
