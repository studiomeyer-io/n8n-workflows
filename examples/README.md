# Sample Provider Payloads

This folder ships realistic sample payloads for smoke-testing the templates without wiring up real providers. The CI (`smoke-test-snippets.yml`) validates that every example is valid JSON. Local smoke pattern below.

## Files

| File | Used by template | Source |
|---|---|---|
| `form-submit.json` | T01 Form to CRM Lead Router | Custom HTML form / Webflow / Tally / Typeform shape |
| `stripe-checkout-completed.json` | T02 Stripe Lifecycle to Slack | Stripe `checkout.session.completed` event |
| `stripe-subscription-created.json` | T02 Stripe Lifecycle to Slack | Stripe `customer.subscription.created` event |
| `slack-history-message.json` | T05 Slack Channel Daily Digest | Slack `conversations.history` API response |

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

The second response includes `{"skipped": true, "reason": "duplicate"}` in the n8n execution log.

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

### Slack `conversations.history` (no curl needed)

Template 05 calls `conversations.history` itself on schedule. To smoke-test the digest summarization without hitting Slack, paste `slack-history-message.json` as test data into the `Slack: Fetch History` node's input pin (Editor, Pin Data) and execute manually.

## Future: full snippet smoke harness

`.github/workflows/smoke-test-snippets.yml` ships a stub that validates JSON-shape only today. The full harness extracts every Code node's `jsCode` from each `workflow.json`, wires the matching example payload as `$input.first()`, and asserts no exception. Tracker: [github.com/studiomeyer-io/n8n-workflows/issues](https://github.com/studiomeyer-io/n8n-workflows/issues).
