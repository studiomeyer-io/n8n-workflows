# Sample Provider Payloads

This folder ships realistic sample payloads for smoke-testing the templates without wiring up real providers. The CI (`smoke-test-snippets.yml`) validates that every example is valid JSON. Local smoke pattern below.

## Files

| File | Used by template | Source |
|---|---|---|
| `form-submit.json` | T01 Form to CRM Lead Router | Custom HTML form / Webflow / Tally / Typeform shape |
| `stripe-checkout-completed.json` | T02 Stripe Lifecycle to Slack | Stripe `checkout.session.completed` event |
| `stripe-subscription-created.json` | T02 Stripe Lifecycle to Slack | Stripe `customer.subscription.created` event |
| `slack-history-message.json` | T05 Slack Channel Daily Digest | Slack `conversations.history` API response |
| `github-issue-opened.json` | T07 GitHub Issues Router | GitHub Issues webhook, `action=opened` |
| `audit-event-signed.json` | T13 Webhook Audit Trail | Generic CRM event used by the audit ingest |

All examples share one fictional customer (Maria Schmidt, +49 170 555 4444, Acme Mittelstand GmbH) so smoke-tests can chain across templates and watch one customer persist across channels.

## Curl recipes

### Unsigned (no HMAC) form submission

```bash
curl -X POST https://your-n8n.example.com/webhook/lead-form \
  -H 'Content-Type: application/json' \
  --data-binary @examples/form-submit.json
```

Expected: HTTP 200 with `{"ok": true, "dealId": "<crm-deal-id>", "temperature": "warm", "score": <0-100>}`. The `temperature` is computed by the BANT scoring rubric, the `dealId` comes from the CRM you targeted.

### Signed form submission (HMAC)

```bash
SECRET="your-32-char-random-secret"
BODY=$(cat examples/form-submit.json)
SIG=$(printf '%s' "$BODY" | openssl dgst -sha256 -hmac "$SECRET" | awk '{print $2}')

curl -X POST https://your-n8n.example.com/webhook/lead-form \
  -H 'Content-Type: application/json' \
  -H "x-form-signature: $SIG" \
  --data "$BODY"
```

Expected: same as unsigned, plus the `Verify Webhook (opt-in)` Code node validates the signature.

### Idempotency replay test

Send the same payload twice. With `IDEMPOTENCY_ENABLED=1`, the second call short-circuits without producing a duplicate CRM deal. Verify by checking your CRM, only one new deal should appear.

```bash
curl -X POST https://your-n8n.example.com/webhook/lead-form \
  -H 'Content-Type: application/json' \
  --data-binary @examples/form-submit.json
# Second call within 5 minutes
curl -X POST https://your-n8n.example.com/webhook/lead-form \
  -H 'Content-Type: application/json' \
  --data-binary @examples/form-submit.json
```

The second call halts cleanly inside the `Idempotency Check` node (`return []`). No downstream node runs, so no duplicate CRM deal is created. The webhook does NOT return 200 to the form provider for the duplicate. The provider may retry within its retry budget; each retry is also caught by the same dedup window. After the provider's retry budget is exhausted you may see a "delivery failed" notification on the provider side, which is the trade-off for not duplicating the side-effect.

### Stripe webhook (signed)

Stripe signs webhooks with a `Stripe-Signature` header in the format `t=<timestamp>,v1=<hmac>`. To replay a sample event:

```bash
SECRET="whsec_your_stripe_webhook_secret"
TIMESTAMP=$(date +%s)
BODY=$(cat examples/stripe-checkout-completed.json)
PAYLOAD="${TIMESTAMP}.${BODY}"
SIG=$(printf '%s' "$PAYLOAD" | openssl dgst -sha256 -hmac "$SECRET" | awk '{print $2}')

curl -X POST https://your-n8n.example.com/webhook/stripe \
  -H 'Content-Type: application/json' \
  -H "Stripe-Signature: t=${TIMESTAMP},v1=${SIG}" \
  --data "$BODY"
```

Expected: HTTP 200, Slack channel gets a `:white_check_mark: New paid customer: Maria Schmidt` message.

### GitHub issue webhook (signed)

GitHub signs webhooks with `X-Hub-Signature-256: sha256=<hex>`:

```bash
SECRET="your-github-webhook-secret"
DELIVERY=$(uuidgen)
BODY=$(cat examples/github-issue-opened.json)
SIG=$(printf '%s' "$BODY" | openssl dgst -sha256 -hmac "$SECRET" | awk '{print $2}')

curl -X POST https://your-n8n.example.com/webhook/github-issues \
  -H 'Content-Type: application/json' \
  -H 'X-GitHub-Event: issues' \
  -H "X-GitHub-Delivery: $DELIVERY" \
  -H "X-Hub-Signature-256: sha256=$SIG" \
  --data "$BODY"
```

Expected: HTTP 200 if `action` is in `[opened, reopened, labeled]`. The Filter Event Type node returns `[]` (empty) for other actions, so no tracker row is created. The downstream tracker (Linear / Jira / ClickUp) creates one ticket and the workflow posts a follow-up comment back on the GitHub issue with the tracker URL.

### T13 Webhook Audit Trail (signed)

The audit ingest signs `<timestamp>.<rawBody>` (Stripe-style) and uses headers `x-audit-timestamp`, `x-audit-signature`, plus optional `x-audit-event-type` + `x-audit-source`:

```bash
SECRET="your-audit-signing-secret"
TS=$(date +%s)
BODY=$(cat examples/audit-event-signed.json)
PAYLOAD="${TS}.${BODY}"
SIG=$(printf '%s' "$PAYLOAD" | openssl dgst -sha256 -hmac "$SECRET" | awk '{print $2}')

curl -X POST https://your-n8n.example.com/webhook/audit \
  -H 'Content-Type: application/json' \
  -H "x-audit-timestamp: $TS" \
  -H "x-audit-signature: $SIG" \
  -H 'x-audit-event-type: deal.create' \
  -H 'x-audit-source: crm' \
  -H "x-request-id: $(uuidgen)" \
  --data "$BODY"
```

Expected: HTTP 200 with `{"ok": true, "id": <int>, "rowHash": "<hex>", "prevHash": "<hex>"}`. The hash chain is serialized via `pg_advisory_xact_lock(hashtext('audit_log_chain:default'))` so two concurrent inserts cannot read the same `prev_hash`. Replay the same `x-request-id` within 5 minutes and the second call halts inside `Idempotency Check`, no row is added to the chain.

To verify the chain integrity from the database:

```sql
WITH chain AS (
  SELECT id, prev_hash, row_hash,
    LAG(row_hash) OVER (ORDER BY id) AS expected_prev
  FROM audit_log
)
SELECT id FROM chain
WHERE expected_prev IS NOT NULL AND expected_prev <> prev_hash;
```

Should return zero rows. Any row id returned indicates the chain was broken at that row, which means either: a direct INSERT bypassed the workflow, the row was tampered with, or there is a production bug to investigate.

### Slack `conversations.history` (no curl needed)

Template 05 calls `conversations.history` itself on schedule. To smoke-test the digest summarization without hitting Slack, paste `slack-history-message.json` as test data into the `Slack: Fetch History` node's input pin (Editor, Pin Data) and execute manually.

## Future: full snippet smoke harness

`.github/workflows/smoke-test-snippets.yml` ships a stub that validates JSON-shape only today. The full harness extracts every Code node's `jsCode` from each `workflow.json`, wires the matching example payload as `$input.first()`, and asserts no exception. Tracker: [github.com/studiomeyer-io/n8n-workflows/issues](https://github.com/studiomeyer-io/n8n-workflows/issues).
