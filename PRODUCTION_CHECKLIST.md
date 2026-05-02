# Production Checklist

Before flipping any template in this repo from import-default to production, walk this list. If a row is unchecked, the deployment is developer-preview, not production.

## Env vars

The four production patterns ship as opt-in nodes gated by env vars. The default import boots clean (env vars unset = pass-through). Production deployments enable them.

| Env var | Type | Required for | Notes |
|---|---|---|---|
| `LEAD_FORM_SIGNING_SECRET` | string (32+ char hex/base64) | T01 Form router | HMAC-SHA256 signing secret. Configure same value in your form provider (Webflow, Tally, Typeform). |
| `STRIPE_WEBHOOK_SECRET` | string (Stripe `whsec_...` format) | T02 Stripe | Get from Stripe Dashboard, Developers, Webhooks. Stripe rotates these on demand. |
| `IDEMPOTENCY_ENABLED` | `1` to enable | all templates | Toggle the in-memory dedup window on. |
| `RATE_LIMIT_ENABLED` | `1` to enable | all templates | Toggle the per-key sliding-window throttle on. |
| `WEBHOOK_INTEGRITY_CHECK_ENABLED` | `1` to enable | T01 + T02 | Master switch for HMAC verification. Without this, any of the templates accepts unsigned requests for testing. Flip to `1` for production. |
| `NODE_FUNCTION_ALLOW_BUILTIN` | comma-separated list | self-hosted only | Must include `crypto` for HMAC, `tls` for SSL watcher, `https` for HTTP fetches. n8n Cloud has these allowed by default for hosted plans, verify in your tenant. Example: `NODE_FUNCTION_ALLOW_BUILTIN=crypto,tls,https`. |
| `MONITOR_TARGETS` | JSON array | T03 uptime | Array of `{url, name, expect_status}` objects to monitor. Default monitors none, you set this. |
| `SSL_DOMAINS` | comma-separated list | T04 SSL | Domains to monitor. Example: `example.com,api.example.com,studiomeyer.io`. |
| `SLACK_DIGEST_CHANNEL` | Slack channel ID | T05 Slack | Where to post the digest. |
| `SLACK_DIGEST_PROVIDER` | `openai` or `anthropic` | T05 Slack | Which LLM to use for the summary. |
| `CRM_TARGET` | `pipedrive`, `hubspot`, `salesforce` | T01 CRM router | Which CRM to push leads into. Default `pipedrive`. |
| `CRM_PIPELINE_HOT_ID` | string | T01 CRM | Stage ID in your CRM for hot leads. |
| `CRM_PIPELINE_WARM_ID` | string | T01 CRM | Stage ID for warm leads. |
| `CRM_PIPELINE_COLD_ID` | string | T01 CRM | Stage ID for cold leads. |

## Credentials in n8n

Configure these in n8n's credential store (Settings, Credentials):

- **Pipedrive API** (or HubSpot OAuth, or Salesforce OAuth) for T01.
- **Stripe API** for T02 (used by some Stripe nodes if you extend the template, the webhook itself does not need it).
- **Slack API** + **Slack incoming webhook URL** for T02, T03, T05.
- **Telegram Bot API** for T03 (alert channel).
- **OpenAI API** + **Anthropic API** for T05.
- **SMTP** or **Brevo** for T05 email digest.

## Redis cluster swap (`$getWorkflowStaticData`)

The default idempotency check uses `$getWorkflowStaticData('global')` which is per-workflow-instance and not atomic. For clustered n8n deployments (multiple workers behind a load balancer) swap to Redis `SET NX EX 300`:

```js
// In the Idempotency Check Code node, replace the in-memory block with:
const Redis = require('ioredis');
const redis = new Redis(process.env.REDIS_URL);

const key = `idempotency:${idempotencyKey}`;
const result = await redis.set(key, '1', 'EX', 300, 'NX');
await redis.quit();

if (result === null) {
  return [];  // duplicate, drop the execution
}
return [{ json: $input.first().json }];
```

Add `ioredis` to the n8n environment via `NODE_FUNCTION_ALLOW_EXTERNAL=ioredis`. n8n Cloud users skip this section, n8n Cloud is single-instance per workspace.

## Reverse-proxy rate limit

The opt-in Rate Limit Code node is defense-in-depth. For real production loads, put the rate limit on a reverse proxy in front of n8n:

**Nginx:**
```nginx
limit_req_zone $binary_remote_addr zone=n8n_webhook:10m rate=20r/s;

location /webhook/ {
    limit_req zone=n8n_webhook burst=40 nodelay;
    proxy_pass http://n8n_upstream;
}
```

**Cloudflare WAF Custom Rule:**
```
(http.request.uri.path contains "/webhook/" and rate(1m) > 60)
```
Action: Block with custom 429 response.

**Traefik:**
```yaml
http:
  middlewares:
    n8n-ratelimit:
      rateLimit:
        average: 20
        burst: 40
        period: 1s
```

## Monitoring

For each template you flip to production, wire one of these observability hooks:

- **Workflow execution metrics.** n8n Pro and self-hosted Enterprise expose Prometheus metrics at `/metrics`. Scrape with Prometheus, alert on `n8n_workflow_execution_total{status="error"}` rising fast.
- **Slack on workflow failure.** Set the n8n env var `N8N_DIAGNOSTICS_ENABLED=true` and configure a workflow-level Error Trigger Workflow that posts to a Slack ops channel on every failed execution.
- **External uptime check.** Use T03 itself, or BetterStack / UptimeRobot, to monitor that the n8n webhook URL responds 2xx (a healthy webhook returns 200 even before any business logic).

## Smoke test before flipping the env var

1. Import the template into a clean n8n instance.
2. Configure the credentials per template README.
3. Send the example payload from `examples/` via curl or Postman.
4. Verify the expected output (Slack message, CRM record, alert, etc).
5. Send the example payload again. Verify the idempotency dedup fires (second call short-circuits without producing a duplicate output).
6. Send a payload with a wrong HMAC. Verify the Verify Webhook node rejects with HTTP 401.
7. Send 70 payloads in 5 minutes. Verify the Rate Limit node rejects after 60 with HTTP 429.
8. Cause an error in the downstream API (drop credentials, point at a wrong URL). Verify the error branch fires and the fallback path produces a graceful response.

## Pre-launch checklist

Copy-paste into your project tracker:

- [ ] All env vars from the table above set in n8n's environment.
- [ ] All credentials configured in n8n's credential store.
- [ ] Idempotency wired to Redis if you have multi-worker n8n.
- [ ] Reverse-proxy rate limit configured if your trigger is a public webhook.
- [ ] Workflow execution metrics scraped or Error Trigger Workflow wired.
- [ ] External uptime check on the webhook URL.
- [ ] Smoke-tested the 8 cases from the section above.
- [ ] Reviewed the template's specific Common Gotchas section in its README.
- [ ] Activated the workflow.

## What about end-to-end live tests?

Each template ships hardened (production-pattern wired) but not end-to-end live-tested against real production backends. The README of each template documents what live test would close the gap. T01 needs a real Pipedrive instance + real form submission. T02 needs real Stripe webhook events. T03 needs a real production schedule cycle. T04 needs a real expiring cert. T05 needs a real Slack workspace.

If you wire one of these and run an end-to-end test, please open a PR adding your trace as a section in the template's README under "Live verification". This helps the next builder.
