<!-- studiomeyer-mcp-stack-banner:start -->
> **Part of the [StudioMeyer MCP Stack](https://studiomeyer.io)**, Built in Mallorca · ⭐ if you use it
<!-- studiomeyer-mcp-stack-banner:end -->

# Template Title

> One-sentence value prop. What does the builder get? Be concrete.

![Cover](./cover.png)

## What this does

Two short paragraphs. First paragraph = the data flow as a single sentence with arrows ("trigger fires, workflow normalizes payload, business logic decides, output goes to <destination>"). Second paragraph = the killer phrase someone searching for this template will resonate with ("the result is X without Y, plus the four production patterns that other templates skip").

## Architecture

```
[Trigger]                         ← raw body / signed request if applicable
    │
    ▼
[Verify Webhook (opt-in)]         ← <PROVIDER>_SIGNING_SECRET
    │
    ▼
[Rate Limit (opt-in)]             ← RATE_LIMIT_ENABLED=1
    │
    ▼
[Idempotency Check (opt-in)]      ← IDEMPOTENCY_ENABLED=1
    │
    ▼
[Normalize Payload]
    │
    ▼
[Business Logic]
    │
    ▼
[Output A]                        ← onError: continueErrorOutput
    │       │
    └───────┼──── error ────► [Fallback Code Node]
            ▼                       │
        [Output B]                  ▼
                            [Structured Error Log]
```

## Setup

1. **Import this workflow** (workflow.json in this folder).
2. **Configure the SET-ME markers.** Yellow sticky notes flag every spot that needs your config.
3. **Add credentials** (provider-specific, see Credentials checklist below).
4. **Set production-pattern env vars** in your n8n environment (see Production patterns below). Default-off so the import boots clean.
5. **Wire up your trigger** (provider-specific instructions below).
6. **Test.** Send a sample payload, verify the expected output.

### Provider-specific setup

- **<Provider>:** Specific instructions per provider. Webhook URL configuration. Event subscriptions. API token generation steps.

## Multi-provider switch

(Skip this section if no LLM is involved.)

The workflow has a `Set Provider` node followed by a `Route by Provider` switch. Default value is `openai`. Change to `anthropic` (or add your own branch with a third LLM) without rebuilding the rest of the flow. Both branches converge in `Normalize LLM Output` which extracts the reply text from either provider's response shape.

## Extending

**<First extension idea>.** One paragraph in flowing prose explaining what to add and where. Reference specific node names from the workflow.

**<Second extension idea>.** Same shape.

**<Third extension idea>.** Same shape.

## Cost notes

Per execution (assuming average payload):

| Component | Cost (Stand 2026-05) | Per-execution cost |
|---|---|---|
| **<External API>** | varies | ~$<X> per execution |
| **OpenAI gpt-5.4-mini** (when LLM applicable) | $0.75 / 1M input + $4.50 / 1M output | ~$<X> per execution |

**Worked example at <typical-volume>/month:**

| Stack | Cost | Total /mo |
|---|---|---|
| <stack>  | ~$<X>/mo | **~$<X>/mo** |

The error branch fires on external API failures. It writes one structured error log per failure. At a healthy 99.5% success rate this adds <0.5% to your bill.

## Common gotchas

- **<First gotcha>.** Explain what goes wrong, why, and how to fix it. One paragraph.
- **<Second gotcha>.** Same.
- **<Third gotcha>.** Same.
- **n8n core HTTP request body shape.** The HTTP Request node's body parameter expects a string, not a JSON object. Wrap with `JSON.stringify({...})` in expressions.
- **n8n error syntax.** Inline error pin uses `{{ $json.error.message }}`. Separate Error Trigger Workflow uses `{{ $json.execution.error.message }}` + `{{ $json.workflow.name }}`. Often-quoted `{{ $error.message }}` does not exist.

## Production patterns

Four patterns ship in `workflow.json` as actual nodes, three opt-in via env vars and one always-on error branch. The opt-in nodes pass through when their env var is unset, so the default import boots clean.

**Idempotency** (opt-in, `IDEMPOTENCY_ENABLED=1`). The `Idempotency Check` Code node holds a 5-minute in-memory window of seen `<idempotency-key>` values via `$getWorkflowStaticData('global')` and short-circuits duplicates. For clustered n8n deployments, swap the in-memory block for Redis `SET NX EX 300`. The node has the swap pattern in its comments.

**Rate limiting** (opt-in, `RATE_LIMIT_ENABLED=1`). The `Rate Limit` Code node caps each `<rate-limit-key>` at 60 requests in a 5-minute sliding window. Map bounded at 5000 entries with eviction. For real production loads, put rate limiting on a reverse proxy (Nginx `limit_req_zone`, Cloudflare WAF, Traefik) and keep this node as defense-in-depth.

**Webhook HMAC verification** (opt-in, `<PROVIDER>_SIGNING_SECRET`). The `Verify Webhook` Code node computes HMAC-SHA256 of the raw body using the configured secret and compares against the provider signature header with `crypto.timingSafeEqual`. Length-guard before the timing-safe compare prevents `RangeError` DoS from a 1-char signature. Without HMAC, an attacker who guesses your webhook URL can spike your bill.

**Error branches** (always on). Every external API call has `On Error: Continue (Using Error Output)` enabled. The error pin lands at a fallback Code node which builds a structured error log and writes a graceful response. The error syntax is `{{ $json.error.message }}`, not `{{ $error.message }}` (does not exist) and not `{{ $json.execution.error.message }}` (Error Trigger Workflow only, not inline pins).

## Hard compatibility floor

**Minimum n8n version with CVE-2026-27493 fix:** >= 2.9.3 (stable channel) / >= 2.10.1 (latest / beta channel) / >= 1.123.22 (1.x LTS). CVE-2026-27493 is an unauthenticated RCE in Form nodes (CVSS 9.5). This template does not use Form nodes itself, but you should still upgrade for general security. The pre-activation check on n8n 2.15.0 was used to validate every node type-string in this template.

## Tech stack matrix

| Component | Version | Cost | Free tier | Required when |
|---|---|---|---|---|
| n8n | >= 2.10.1 (CVE-2026-27493 floor) | self-hosted free / Cloud $20/mo | n8n Cloud trial | always |
| <External provider> | latest stable | varies | trial available | always |
| OpenAI (default for LLM templates) | gpt-5.4-mini | $0.75 / 1M input + $4.50 / 1M output | $5 trial credit | provider = openai |

## Credentials checklist

Before activation, create these credentials in n8n:

- [ ] **<External provider>** (provider-specific). Setup webhook URL in their dashboard pointing at your n8n instance.
- [ ] **OpenAI API** (`openAiApi`) OR **Anthropic API** (`anthropicApi`) (when LLM applicable). Get key at platform.openai.com / console.anthropic.com.
- [ ] **Webhook signing secret (recommended).** Set the n8n env var `<PROVIDER>_SIGNING_SECRET` to a strong random string and configure the same secret in your provider dashboard.

## Need cross-session memory?

This repo is intentionally memory-free. If you want the workflow to remember state across executions (the bot recognizes returning users, the support agent picks up where the previous conversation left off, the voice agent has caller history), see the sister repo:

**[studiomeyer-io/n8n-templates](https://github.com/studiomeyer-io/n8n-templates)** ships eight templates that wire [StudioMeyer Memory](https://memory.studiomeyer.io) (a hosted MCP backend with knowledge graph, semantic search, multi-tenant isolation) into the same production-pattern foundation.

## Related templates

- [01 - Form to CRM Lead Router](../01-form-to-crm-lead-router/)
- [02 - Stripe Lifecycle to Slack](../02-stripe-lifecycle-to-slack/)
- [03 - Uptime Monitor with Alerts](../03-uptime-monitor-with-alerts/)
- [04 - SSL Certificate Expiry Watcher](../04-ssl-certificate-expiry-watcher/)
- [05 - Slack Channel Daily Digest](../05-slack-channel-daily-digest/)

---

*Built by [StudioMeyer](https://studiomeyer.io) in Mallorca. Issues + ideas at [github.com/studiomeyer-io/n8n-workflows/issues](https://github.com/studiomeyer-io/n8n-workflows/issues).*
