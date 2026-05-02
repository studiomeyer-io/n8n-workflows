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
| `NOTION_API_TOKEN` | string (Notion `secret_*` token) | T11, T15 | Internal Integration Token from notion.so/my-integrations. |
| `NOTION_DATABASE_ID` | string (32-char UUID) | T11, T15 | Target database ID. Database must be shared with the integration. |
| `EMAIL_FROM_WHITELIST` | comma-separated domains | T11 | Optional. Only mails from these domains are processed. |
| `EMAIL_SUBJECT_INCLUDE` | comma-separated keywords | T11 | Optional. Only mails whose subject contains any of these. |
| `PG_SYNC_QUERY` | string (SELECT with `$1` placeholder) | T12 | The SELECT statement that drives the sync. Always include `LIMIT`. |
| `PG_SYNC_HWM_INITIAL` | string (ISO-8601) | T12 | First-run high-water-mark seed. After first run, workflow state takes over. |
| `PG_SYNC_HWM_FIELD` | string | T12 | The timestamp column name. Default `updated_at`. |
| `PG_SYNC_DEDUP_KEY` | string | T12 | The row primary key column. Default `id`. |
| `PG_SYNC_COLUMN_ORDER` | comma-separated column names | T12 | The Sheets column projection order. |
| `GOOGLE_SHEETS_ID` | string | T12 | Target spreadsheet ID. |
| `GOOGLE_SHEETS_RANGE` | string | T12 | Tab + range. Example: `Sheet1!A1:Z`. |
| `MAX_ROWS_PER_RUN` | integer | T12 | Default 5000. Defends against runaway queries. |
| `AUDIT_SIGNING_SECRET` | string (32+ char hex/base64) | T13 | HMAC-SHA256 signing secret for the audit ingest endpoint. |
| `AUDIT_REPLAY_WINDOW_S` | integer (seconds) | T13 | Default 300. Replay window for signed audit events. |
| `AUDIT_RATE_LIMIT_PER_IP` | integer | T13 | Default 60. Max requests per IP in the 5-min sliding window. |
| `MAX_BODY_BYTES` | integer | T13 | Default 1048576 (1MB). Hard cap on the audit-event body size. |
| `SLACK_SECURITY_WEBHOOK` | URL | T13 | Slack webhook for auth + capacity + database security alerts. |
| `TELEGRAM_WEBHOOK_SECRET` | string | T14 | Same value used in `setWebhook?secret_token=`. Validated by the trigger node. |
| `TARGET_LANG` | string (BCP-47 or English name) | T14 | Translation target language. Default `English`. |
| `LLM_PROVIDER` | `openai` or `anthropic` | T14, T15 (when summary on) | Selects the LLM branch in the multi-provider Switch. |
| `YOUTUBE_CHANNEL_IDS` | comma-separated `UC...` IDs | T15 | The list of channels to watch. Cap 50. |
| `LLM_SUMMARY_ENABLED` | `1` to enable | T15 | Optional. When set, each new video gets an LLM summary in the Notion row. |
| `MAX_VIDEOS_PER_CHANNEL_PER_RUN` | integer | T15 | Default 10. First-run defense for high-volume channels. |
| `SLACK_OPS_WEBHOOK` | URL | T11, T12, T15 | Slack webhook for non-security ops alerts (Notion failure, Sheets append failure, RSS fetch failure). |

## Credentials in n8n

Configure these in n8n's credential store (Settings, Credentials):

- **Pipedrive API** (or HubSpot OAuth, or Salesforce OAuth) for T01, T06.
- **Stripe API** for T02 (used by some Stripe nodes if you extend the template, the webhook itself does not need it).
- **Slack API** + **Slack incoming webhook URL** for T02, T03, T05, T11, T12, T13, T15.
- **Telegram Bot API** for T03 (alert channel) + T14 (translator bot).
- **OpenAI API** + **Anthropic API** for T05, T14, T15 (when LLM is involved).
- **SMTP** or **Brevo** for T05 email digest.
- **IMAP** for T11.
- **Postgres** for T12, T13.
- **Google Sheets OAuth2** for T12.
- **GitHub** webhook signing secret for T07. **Calendly** v2 webhook signing for T06. **X / LinkedIn / Discord** OAuth for T08. **Google Calendar OAuth2** + **Microsoft Graph OAuth2** for T09. **CSV upload signing secret** for T10. **Notion API token** for T11, T15. **Audit ingest signing secret** for T13. **Telegram bot token** + **secret_token** for T14.

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
