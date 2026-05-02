# Template Status

> **Single source of truth for what is hardened, what is in-progress, where the distribution push stands.** Updated per release. Last update: 2026-05-02 (v0.2.0 release with templates 06-10).

## Per-template status

| # | Template | Status | What is wired | What is pending |
|---|---|---|---|---|
| 01 | [Form to CRM Lead Router](./templates/01-form-to-crm-lead-router/) | **Hardened** (v0.1.0) | All 4 production patterns as nodes (HMAC verify with `LEAD_FORM_SIGNING_SECRET`, rate limit, idempotency on form submission ID, error branch with graceful response). BANT scoring code node. Multi-CRM Switch (Pipedrive default, HubSpot + Salesforce as documented branches). Cover image generated. Live-import + pre-activation-check passed against n8n.studiomeyer.io v2.15.0. | End-to-end test with real CRM credentials. |
| 02 | [Stripe Lifecycle to Slack](./templates/02-stripe-lifecycle-to-slack/) | **Hardened** (v0.1.0) | All 4 production patterns. Stripe-specific HMAC with `Stripe-Signature` header (timestamp + v1 hash, replay-window check). Per-event-type Slack message templates (`checkout.session.completed`, `customer.subscription.created`, `customer.subscription.updated`, `customer.subscription.deleted`, `invoice.payment_failed`). Rate limit + idempotency on `event.id`. Cover image generated. Live-import + pre-activation-check passed. | End-to-end test with real Stripe webhook events. |
| 03 | [Uptime Monitor with Alerts](./templates/03-uptime-monitor-with-alerts/) | **Hardened** (v0.1.0) | Schedule trigger (every 5 min default). Multi-target HTTP check (loop over configured URLs). Status detection with retry-with-backoff. Slack + Telegram alert branches. Idempotency on consecutive-failure dedup (do not spam alerts on persistent outages). Rate limit + error branches. Cover image generated. Live-import + pre-activation-check passed. | End-to-end test in a production schedule cycle. |
| 04 | [SSL Certificate Expiry Watcher](./templates/04-ssl-certificate-expiry-watcher/) | **Hardened** (v0.1.0) | Schedule trigger (daily 09:00 UTC default). Multi-domain TLS check via `tls.connect`. Days-until-expiry calculation. Three-tier alert (warning <30 days, urgent <14 days, critical <7 days). Slack alert branch. Rate limit + error branches. Cover image generated. Live-import + pre-activation-check passed. | End-to-end test against a domain with a real expiring cert. |
| 05 | [Slack Channel Daily Digest](./templates/05-slack-channel-daily-digest/) | **Hardened** (v0.1.0) | Schedule trigger (daily). Slack `conversations.history` fetch with cursor pagination. Multi-provider LLM summarization (OpenAI default, Anthropic optional, Claude Haiku 4.5 fallback chain). Email + Slack-post output. All 4 production patterns. Cover image generated. Live-import + pre-activation-check passed. | End-to-end test with a real Slack workspace. |
| 06 | [Calendly to CRM Sync](./templates/06-calendly-to-crm-sync/) | **Hardened** (v0.2.0) | All 4 production patterns. Calendly v2 webhook signing format (`Calendly-Webhook-Signature: t=<ts>,v1=<hmac>` over `<timestamp>.<rawBody>`) with 5-min replay window. Idempotency on `event.uri + invitee.uri`. Multi-CRM Switch (Pipedrive default, HubSpot, Salesforce) with explicit fallback output to `Error Fallback`. Lifecycle classification (booked / canceled / no_show). Cover image generated. Live-import + pre-activation-check passed. | End-to-end test with a real Calendly webhook subscription. |
| 07 | [GitHub Issues Router](./templates/07-github-issues-to-tracker/) | **Hardened** (v0.2.0) | All 4 production patterns. GitHub `X-Hub-Signature-256` HMAC with `sha256=<hex>` prefix-strip. Idempotency on `X-GitHub-Delivery`. Multi-tracker Switch (Linear default GraphQL, Jira REST `/rest/api/2/issue` with HTTP Basic auth, ClickUp REST `/list/{id}/task`). `Filter Event Type` returns `[]` for unforwarded actions to halt the branch cleanly. Followup comment back on the GitHub issue with the tracker URL. Cover image generated. Live-import + pre-activation-check passed. | End-to-end test with a real GitHub webhook + Linear / Jira / ClickUp account. |
| 08 | [RSS to Multi-Channel Social](./templates/08-rss-to-multi-channel-social/) | **Hardened** (v0.2.0) | Schedule trigger (every 30 min default). Multi-feed fan-out from `RSS_FEEDS` env, lightweight RSS / Atom parser without external XML lib. Per-feed-host rate limit (12 fetches / hour / host) + 7-day idempotency on item guid + per-channel error branches. Multi-channel Switch (X v2 OAuth 1.0a, LinkedIn `/v2/ugcPosts`, Discord webhook). Pre-formatted per-channel post text (X 240 char trim, LinkedIn longer, Discord 1900 char + embed). Cover image generated. Live-import + pre-activation-check passed. X pricing reflects Feb 2026 pay-per-use default + legacy Basic $200/mo for existing subscribers. | End-to-end test with real X / LinkedIn / Discord credentials and a live RSS source. |
| 09 | [Calendar Conflict Detector](./templates/09-calendar-conflict-detector/) | **Hardened** (v0.2.0) | Schedule trigger (daily 06:00 UTC default). Multi-calendar fan-out from `CALENDAR_IDS` env. Multi-provider Switch (Google Calendar v3 `events.list?singleEvents=true&orderBy=startTime`, Microsoft Graph `/users/{id}/calendarView`). Pair-wise interval-overlap algorithm across calendars. Per-calendar rate limit + 24-hour idempotency on `sha256(eventA.id + eventB.id)`. Outlook timezone normalization with safe `Z` append (warns on non-UTC `Prefer` headers). Cover image generated. Live-import + pre-activation-check passed. | End-to-end test with a real Google or Outlook calendar. |
| 10 | [CSV Bulk Validator](./templates/10-csv-bulk-validator/) | **Hardened** (v0.2.0) | Webhook with `rawBody: true` for HMAC verification. HMAC + replay-window protection (`x-csv-timestamp` + `x-csv-signature` over `<timestamp>.<rawBody>`, 5-min default). Idempotency on `sha256(rawBody)`. Quote-aware RFC 4180 CSV parser with BOM strip + configurable delimiter + `MAX_BODY_BYTES` + `MAX_ROWS` caps. Pre-compiled regex patterns from operator-controlled `VALIDATION_SCHEMA` env, with ReDoS heuristic (200-char cap + nested-quantifier refusal). Per-row sanitization, structured `{valid, invalid, summary}` response. `Parse CSV` error output wired to `Error Fallback`. Cover image generated. Live-import + pre-activation-check passed. | End-to-end test with a real upstream client signing requests. |

## Repo-level status

| Item | Status |
|---|---|
| MIT License + CONTRIBUTING + SECURITY + COC + ECOSYSTEM | Done |
| GitHub Actions CI (workflow.json validation, em-dash guard, forbidden-keys check, credential-leak scan) | Done |
| `templates/_TEMPLATE/` skeleton on v0.1.0 standard | Done |
| Cover images (Flux 2 Max, 1216x640, navy + gold) for all 5 templates | Done |
| Comparison tables vs other public n8n template repos | Done |
| Hard compatibility floor (n8n 2.10.1+ for CVE-2026-27493) declared | Done |
| Honest production-readiness framing ("production-pattern hardened, not a one-click prod deploy") | Done |
| Pricing in cost notes synced to Stand 2026-05 | Done |
| Distribution push (n8n.io/workflows + awesome-n8n-templates + dev.to + Reddit + LinkedIn) | **Pending** initial real-user feedback |

## What "hardened" means

Each template has been through the same five-phase pass:

1. **Audit** against the internal quality checklist (8 mandatory README sections, sticky note color palette 5/6/7, no em-dashes, no forbidden top-level keys).
2. **Production patterns** as actual opt-in nodes in `workflow.json`: Verify Webhook (HMAC where applicable), Rate Limit, Idempotency Check (gated by env vars, default-off, pass-through when unset). Plus always-on Error-Output branch on every external API call wired to a fallback Code node + structured error log.
3. **README polish** to Reddit-readable level: ASCII architecture diagram, multi-provider switch section (when LLM is involved), concrete cost numbers with current 2026 LLM pricing, 3-4 extending patterns, comparison-aware framing, live-verification table or honest "structurally validated" note.
4. **Cover image** verified Brand-conform (1216x640 navy + gold via Flux 2 Max).
5. **Quality Gate** parallel pass with three dedicated agents (Critic for bugs + Architect for repo-convention compliance + Research for current 2026 standards). All AMBER findings fixed before commit. Plus structural validation via the live n8n.studiomeyer.io pre-activation check.

A template is "hardened" when all five phases are green and the internal self-check passes.

## What is NOT yet done

- **End-to-end smoke tests against live production backends.** Each template has been live-imported into n8n.studiomeyer.io v2.15.0 and pre-activation-check passed (all node types recognized, all connections valid). End-to-end live triggers against real backends (real Pipedrive instance for T01, real Stripe webhook events for T02, real production schedule cycle for T03, real expiring cert for T04, real Slack workspace for T05) are part of the next pass when those provisioning items land.
- **Distribution push** to n8n.io/workflows, awesome-n8n-templates PR, dev.to long-form articles, Reddit r/n8n, LinkedIn DACH PDF carousels. Pending initial real-user feedback. Plan: T02 Stripe template ships first to Reddit as the SaaS-builder hook (Stripe + Slack signed webhooks is a well-searched pain).
- **Memory variant cross-link.** Each template references [studiomeyer-io/n8n-templates](https://github.com/studiomeyer-io/n8n-templates) for users who need cross-session memory. The Memory variant repo cross-references back. Both repos stay focused on their own scope.

## Public claims discipline

A repo-internal rule: **public repo description never claims more than the weakest production-ready path in the repo claims.**

GitHub repo description: "Production n8n workflows. Hardened patterns, multi-provider LLM, no memory required."
Top-level README: "Production-pattern hardened, not a one-click production deploy yet" with explicit per-template status.
This `STATUS.md`: ground truth, updated per release.

If you find a discrepancy between any of these, file an issue. The README and STATUS.md are the source of truth, the GitHub description tracks them.

---

*Built by [StudioMeyer](https://studiomeyer.io) in Mallorca. Issues + ideas at [github.com/studiomeyer-io/n8n-workflows/issues](https://github.com/studiomeyer-io/n8n-workflows/issues).*
