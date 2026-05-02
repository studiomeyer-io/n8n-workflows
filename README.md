<!-- studiomeyer-mcp-stack-banner:start -->
> **Part of the [StudioMeyer MCP Stack](https://studiomeyer.io)**, Built in Mallorca · ⭐ if you use it
<!-- studiomeyer-mcp-stack-banner:end -->

<div align="center">

# n8n Workflows · Production Patterns

**Drop-in n8n workflows that ship the production patterns most public templates skip.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![n8n compatible](https://img.shields.io/badge/n8n-2.10.1%2B-FF6E5C.svg)](https://n8n.io)
[![Templates](https://img.shields.io/badge/templates-15%20live-brightgreen.svg)](#templates)
[![CI](https://github.com/studiomeyer-io/n8n-workflows/actions/workflows/validate-workflows.yml/badge.svg)](https://github.com/studiomeyer-io/n8n-workflows/actions)

CRM router · Stripe · uptime · SSL · Slack digest · Calendly · GitHub · RSS · calendar · CSV · Email-Notion · Postgres-Sheets · Webhook audit · Telegram translator · YouTube-Notion · no memory required

[Quick Start](#quick-start) · [Templates](#templates) · [Production Patterns](#production-patterns) · [Memory Variant](#memory-variant)

</div>

---

## Why this exists

Most public n8n templates show the happy path and stop. They skip HMAC verification on public webhooks, swallow LLM errors silently, write duplicate records on provider retries, and leave rate limiting as an exercise for the reader. We audited five high-star n8n template repos in April 2026 and the gap was consistent.

This repo closes the gap. Every workflow in here ships four production patterns as opt-in nodes inside `workflow.json`, gated by env vars, default-off so the import boots clean: HMAC webhook verification, idempotency check, rate limit, error branches with graceful fallback. Toggle a single env var to flip a pattern on for production.

These templates are intentionally memory-free. If you want cross-session memory (the bot remembers who called yesterday), use [studiomeyer-io/n8n-templates](https://github.com/studiomeyer-io/n8n-templates) instead. Both repos share the same production-pattern foundation, the difference is whether StudioMeyer Memory is wired in.

## Quick Start

```bash
# 1. Clone or fetch a single workflow
git clone https://github.com/studiomeyer-io/n8n-workflows.git

# 2. Open the template folder you want and copy the workflow.json contents.

# 3. In n8n: Top-right menu, Import from clipboard, paste, Import.

# 4. Yellow sticky notes mark every >> SET ME << spot. Fill them, activate.
```

Detailed walkthrough per template lives inside each `templates/NN-slug/README.md`.

## Templates

| # | Template | Trigger | LLM | Production patterns | Status |
|---|---|---|---|---|---|
| 1 | [Form to CRM Lead Router](./templates/01-form-to-crm-lead-router/) | Form webhook | optional | HMAC, rate limit, idempotency with respond-duplicate gateway, error branch | Hardened (v0.3.1) |
| 2 | [Stripe Lifecycle to Slack](./templates/02-stripe-lifecycle-to-slack/) | Stripe webhook | none | HMAC (Stripe), rate limit, idempotency with respond-duplicate gateway, error branch | Hardened (v0.3.1) |
| 3 | [Uptime Monitor with Alerts](./templates/03-uptime-monitor-with-alerts/) | Schedule cron | none | rate limit, idempotency, error branch | Hardened (v0.1.0) |
| 4 | [SSL Certificate Expiry Watcher](./templates/04-ssl-certificate-expiry-watcher/) | Schedule daily | none | rate limit, error branch | Hardened (v0.1.0) |
| 5 | [Slack Channel Daily Digest](./templates/05-slack-channel-daily-digest/) | Schedule daily | yes (multi-provider) | rate limit, idempotency, error branch | Hardened (v0.1.0) |
| 6 | [Calendly to CRM Sync](./templates/06-calendly-to-crm-sync/) | Calendly v2 webhook | none | HMAC (Calendly v2 + replay-window), rate limit, idempotency with respond-duplicate gateway, error branch | Hardened (v0.3.1) |
| 7 | [GitHub Issues Router](./templates/07-github-issues-to-tracker/) | GitHub webhook | none | HMAC (`X-Hub-Signature-256`), rate limit, idempotency on `X-GitHub-Delivery` with respond-duplicate gateway, error branch | Hardened (v0.3.1) |
| 8 | [RSS to Multi-Channel Social](./templates/08-rss-to-multi-channel-social/) | Schedule cron | none | rate limit (per-feed-host), 7-day idempotency on guid, per-channel error branch | Hardened (v0.2.0) |
| 9 | [Calendar Conflict Detector](./templates/09-calendar-conflict-detector/) | Schedule daily | none | rate limit (per-calendar), 24h idempotency on conflict-pair hash, per-calendar error branch | Hardened (v0.2.0) |
| 10 | [CSV Bulk Validator](./templates/10-csv-bulk-validator/) | Webhook (CSV upload) | none | HMAC + replay-window, rate limit, idempotency on `sha256(rawBody)` with respond-duplicate gateway, ReDoS-protected schema regexes, error branch | Hardened (v0.3.1) |
| 11 | [Email to Notion](./templates/11-email-to-notion/) | IMAP poll | none | filter (sender + subject opt-in), rate limit (Notion writes), idempotency on Message-ID hash, error branch | Hardened (v0.3.0) |
| 12 | [Postgres to Google Sheets Sync](./templates/12-postgres-to-sheets-sync/) | Schedule daily | none | rate limit, idempotency on row PK (24h), `MAX_ROWS_PER_RUN` cap, HWM-only-on-success, error branch | Hardened (v0.3.0) |
| 13 | [Webhook Audit Trail](./templates/13-webhook-audit-trail/) | Webhook (signed event ingest) | none | HMAC + replay-window, rate limit per IP, idempotency, advisory-locked hash-chain across rows, security + capacity Slack alerts | Hardened (v0.3.1) |
| 14 | [Telegram Translator Bot](./templates/14-telegram-translator-bot/) | Telegram | yes (multi-provider) | Telegram secret_token, rate limit per user_id, idempotency on update_id, LLM fallback with `isLlmError` discriminator, error branch | Hardened (v0.3.0) |
| 15 | [YouTube Channel to Notion](./templates/15-youtube-channel-to-notion/) | Schedule daily | optional (multi-provider) | rate limit per host, 90d videoId idempotency, `MAX_VIDEOS_PER_CHANNEL_PER_RUN` cap, optional LLM summary, error branch | Hardened (v0.3.0) |

T01 is the BANT scoring + multi-CRM router (Pipedrive / HubSpot / Salesforce switch). T02 is the Stripe webhook with proper signature verification and per-event-type Slack messages. T03 is the schedule-based HTTP uptime check with retry-with-backoff and Slack/Telegram alerts. T04 is the daily SSL cert expiry watcher across multiple domains. T05 is the multi-provider LLM Slack digest (Claude / OpenAI / Gemini fallback chain). T06 mirrors Calendly v2 booking events into the same multi-CRM Switch as T01 (Pipedrive default). T07 mirrors GitHub issue events into a multi-tracker Switch (Linear default GraphQL, Jira REST, ClickUp REST), then comments back on the GitHub issue with the tracker URL. T08 fans out RSS items into X / LinkedIn / Discord with per-channel error branches and a 7-day in-memory dedup window. T09 polls Google Calendar v3 or Microsoft Graph for the next 7 days and posts a Slack alert per detected double-booking with 24h dedup. T10 accepts a CSV upload (HMAC-signed and replay-window protected when configured) and returns a structured `{valid, invalid, summary}` report. T11 polls an IMAP mailbox and writes filtered emails into a Notion database with attachment-count, message-ID dedup, and Slack-on-Notion-failure. T12 reads a parametrized Postgres SELECT with a high-water-mark, dedupes by row primary key, caps at `MAX_ROWS_PER_RUN`, appends to Google Sheets, and only advances the HWM when the append succeeded. T13 is a generic signed-event ingest endpoint with HMAC + replay-window, an audit table that includes a `prev_hash` -> `row_hash` chain so tampering becomes detectable, plus Slack alerts on signature-fail and rate-limit-hit. T14 is a Telegram bot that detects the source language of any incoming text and replies with a translation in the configured target language, multi-provider Switch (OpenAI default, Anthropic optional). T15 watches a list of YouTube channels via public RSS, dedupes by videoId for 90 days, optionally LLM-summarizes title + description, writes one Notion page per new video.

More templates land per release cadence. See [STATUS.md](./STATUS.md) for ground truth on what is hardened, what is in-progress, and what is on the roadmap.

## Architecture

The shared backbone across every template:

```
[Trigger]
    │
    ▼
[Verify Webhook (opt-in)]        ← HMAC where applicable
    │
    ▼
[Rate Limit (opt-in)]            ← per-key sliding window, default 60/5min
    │
    ▼
[Idempotency Check (opt-in)]     ← in-memory or Redis SET NX EX
    │
    ▼
[Normalize Payload]              ← provider-specific shape into normalized schema
    │
    ▼
[Business logic]                 ← varies per template
    │
    ▼
[Outputs]                        ← Slack / CRM / Database / etc
```

The four opt-in nodes (Verify, Rate Limit, Idempotency, plus the always-on Error Branch on every external API call) are the production-pattern foundation. Each node is gated by an env var. When the env var is unset the node passes through with no side effects, so the workflow runs clean on import without configuration.

## Prerequisites

Every template needs:

1. **n8n with CVE-2026-27493 fix.** That means **>= 2.9.3** on the 2.x stable channel (n8n.io default), **>= 2.10.1** on the 2.x latest/beta channel, or **>= 1.123.22** on the 1.x LTS channel. CVE-2026-27493 is an unauthenticated RCE in Form nodes (CVSS 9.5, fixed Feb 2026). None of these templates use Form nodes themselves, but you should not run a vulnerable n8n in any case.
2. **Node `crypto` builtin allowed (self-hosted only).** Set the n8n env var `NODE_FUNCTION_ALLOW_BUILTIN=crypto` in your self-hosted instance. n8n Cloud has this allowed by default for hosted plans, verify in your tenant before flipping HMAC on in production.
3. **Provider-specific credentials.** Documented per template (Stripe API key, Slack webhook URL, Pipedrive API token, etc).

## Production patterns

Built into every template's workflow.json (verifiable when you import):

| Pattern | Why it matters | How it ships |
|---|---|---|
| **HMAC webhook verification** | Public webhooks without signature verification can be hit by anyone. At LLM scale that is a $1000 bill in 5 minutes. | Code node right after the webhook trigger that verifies the provider signature (Stripe `Stripe-Signature`, generic HMAC-SHA256) with `crypto.timingSafeEqual` and rejects unsigned requests. Length-guard before the timing-safe compare prevents `RangeError` DoS. Gated by `<PROVIDER>_SIGNING_SECRET` env var. |
| **Idempotency check** | Trigger providers retry on 5xx. Without dedup, every retry creates a duplicate record and a duplicate downstream call. | Code node that holds a 5-minute in-memory window of seen idempotency keys via `$getWorkflowStaticData` and short-circuits duplicates. Swap to Redis `SET NX EX 300` for clustered n8n deployments (snippet in code-node comments). Gated by `IDEMPOTENCY_ENABLED=1`. |
| **Rate limiting** | Same reason as HMAC. Even with HMAC, a stolen secret needs throttling. | Per-key sliding-window Code node, 60 requests / 5 min default, bounded at 5000 entries with eviction. Gated by `RATE_LIMIT_ENABLED=1`. For real production loads put rate limiting on a reverse proxy (Nginx `limit_req_zone`, Cloudflare WAF, Traefik) and keep this node as defense-in-depth. |
| **Error branches** | LLM 429 / 500 / timeouts happen. External API outages happen. Without an error branch, the workflow silently fails and the user gets nothing. | Always on. Every external API call has `On Error: Continue (Using Error Output)` enabled, the error pin lands at a fallback Code node that produces a graceful response and writes a structured error log. The correct n8n syntax is `{{ $json.error.message }}` for inline pins. The often-quoted `{{ $error.message }}` does not exist. |

## Memory Variant

If you need cross-session memory (the bot remembers what was discussed yesterday, the support agent recognizes returning customers by email, the voice agent picks up the previous call's context), use the sister repo:

**[studiomeyer-io/n8n-templates](https://github.com/studiomeyer-io/n8n-templates)** ships eight templates that wire [StudioMeyer Memory](https://memory.studiomeyer.io) (a hosted MCP backend with knowledge graph, semantic search, multi-tenant isolation) into the same production-pattern foundation. Voice agents with caller history, customer support with prior tickets, personal assistants with long-term context, restaurant bots with phone-number-keyed loyalty.

Both repos use the same opt-in node pattern, the same CI guards, the same hard n8n version floor. The split is intentional: this repo stays focused on production patterns without forcing a Memory dependency, the other repo stays focused on what changes when you add Memory.

## How we compare to other public n8n template repos

We audited five high-star public n8n template / workflow repos in April 2026 ([awesome-n8n-templates](https://github.com/enescingoz/awesome-n8n-templates), [n8n-workflows](https://github.com/Zie619/n8n-workflows), and three others) plus a sample of [n8n.io/workflows](https://n8n.io/workflows) listings. None of them ship the production patterns above. Most stop at the happy path:

| Capability | Most public n8n template repos | This repo |
|---|---|---|
| Workflow runs once you import | yes | yes |
| Sticky notes | sometimes | always (every SET-ME marker) |
| Cover image | sometimes | always (1216x640, suite-consistent) |
| Webhook HMAC verification | none we found | opt-in node, env-var-gated |
| Idempotency pattern | none we found | opt-in node, in-memory or Redis |
| Rate limiting | none we found | opt-in node, sliding window |
| Error-output branches with correct n8n syntax | none we found | always-on, with fallback Code node |
| Hard n8n minVersion floor with CVE awareness | rare | declared, CVE-2026-27493 cited |
| MIT license | usually | yes |
| Open governance (CONTRIBUTING + COC + SECURITY + ECOSYSTEM) | rare | yes |
| Repo CI that validates workflows | rare | GitHub Actions, blocks merges on broken refs / em-dashes / forbidden API keys / live credentials |

The middle four rows are the gap. We close them with opt-in node wiring inside every workflow.json.

## FAQ

**Are these production-ready?** Honest answer: production-pattern hardened, not a one-click production deploy. The four production patterns ship as opt-in nodes (gated by env vars, default-off). When you flip them on you get a hardened workflow. End-to-end smoke tests against live production backends are your responsibility, see [PRODUCTION_CHECKLIST.md](./PRODUCTION_CHECKLIST.md) for the env vars + signing secrets + monitoring you need before flipping these to production. CI blocks workflow.json files with em-dashes, missing references, the n8n-API-rejected `meta`/`staticData`/`versionId`/`id`/`tags` keys, and obvious credential leaks (literal API keys, Bearer tokens, JWTs).

**Can I use this with n8n Cloud?** Yes. All templates run unchanged on n8n Cloud, n8n Self-Hosted, n8n Docker, and the n8n Desktop app. Webhook trigger URLs are auto-generated by n8n.

**What is the cost per execution?** Varies per template. Most are zero (no LLM, no paid API). T05 Slack Digest with LLM costs roughly $0.001 to $0.005 per execution depending on channel volume and provider. Detailed cost tables in each template's README.

**Why a hard n8n version floor?** [CVE-2026-27493](https://nvd.nist.gov/vuln/detail/CVE-2026-27493) (CVSS 9.5) is an unauthenticated RCE in Form nodes, fixed Feb 2026. The patch is in **2.9.3 (stable channel)**, **2.10.1 (latest channel)**, and **1.123.22 (LTS channel)**. The README badge shows 2.10.1+ as the simplest single-line ask, but any of the three patched-version-or-newer combinations works.

**Why no memory layer?** This repo is intentionally memory-free. Use [studiomeyer-io/n8n-templates](https://github.com/studiomeyer-io/n8n-templates) if you want cross-session memory. The split keeps each repo focused on what it does best.

**How do I contribute?** Open a [template request issue](https://github.com/studiomeyer-io/n8n-workflows/issues/new) so we can confirm scope. Then copy `templates/_TEMPLATE/`, fill it in, smoke-test in your own n8n, open a PR. The [CONTRIBUTING.md](./CONTRIBUTING.md) covers the full bar.

**Why is the workflow.json so verbose?** Sticky notes. The yellow notes mark every SET-ME spot for the importing builder. n8n's own template-marketplace creator-hub flags missing sticky notes as the #1 rejection reason for new submissions. We over-comment on purpose.

**Where do I report a security issue?** [SECURITY.md](./SECURITY.md). Email `hello@studiomeyer.io` with subject `[security] n8n-workflows`. We aim for 48-hour acknowledgement and a 7-day patch on high-severity issues.

## Repo structure

```
n8n-workflows/
├── README.md                       # this file
├── STATUS.md                       # per-template ground truth
├── PRODUCTION_CHECKLIST.md         # env vars + secret tokens + monitoring
├── ECOSYSTEM.md                    # the rest of the StudioMeyer toolkit
├── CHANGELOG.md
├── CODE_OF_CONDUCT.md
├── CONTRIBUTING.md
├── SECURITY.md
├── LICENSE                         # MIT
├── .github/
│   ├── FUNDING.yml
│   ├── ISSUE_TEMPLATE/             # bug + template-request
│   ├── PULL_REQUEST_TEMPLATE.md
│   └── workflows/                  # CI: workflow validation, em-dash guard
├── examples/                       # sample provider payloads
└── templates/
    ├── _TEMPLATE/                  # skeleton for new contributions
    ├── 01-form-to-crm-lead-router/
    ├── 02-stripe-lifecycle-to-slack/
    ├── 03-uptime-monitor-with-alerts/
    ├── 04-ssl-certificate-expiry-watcher/
    ├── 05-slack-channel-daily-digest/
    ├── 06-calendly-to-crm-sync/
    ├── 07-github-issues-to-tracker/
    ├── 08-rss-to-multi-channel-social/
    ├── 09-calendar-conflict-detector/
    ├── 10-csv-bulk-validator/
    ├── 11-email-to-notion/
    ├── 12-postgres-to-sheets-sync/
    ├── 13-webhook-audit-trail/
    ├── 14-telegram-translator-bot/
    └── 15-youtube-channel-to-notion/
```

Each template folder is self-contained. Copy any one of them out of this repo and it still works.

## Quality Gate

Every template in this repo is held against an internal quality standard. Each template README must include these sections in order: StudioMeyer MCP Stack banner, title + cover, what this does, architecture (ASCII diagram), setup (numbered steps), multi-provider switch (when LLM is involved), extending (3-4 ideas), cost notes, common gotchas, production patterns, hard compatibility floor, tech stack matrix, credentials checklist, related templates, footer. See [CONTRIBUTING.md](./CONTRIBUTING.md) for the full checklist.

In addition every template ships:

- No em-dashes (LLM-content signature, downranked by indexers)
- No real credentials in the committed `workflow.json`
- Multi-provider LLM switch when an LLM call is involved
- A Flux-generated cover image (`cover.png`)
- A 3-agent code review (analyst + critic + research) on substantial changes

CI enforces the structural pieces. The editorial pieces (tone, sticky-note clarity, naming) are reviewed by maintainers per PR.

## Versioning

Repo follows [Semantic Versioning](https://semver.org/). PATCH for bug fixes in templates. MINOR for new templates or feature additions. MAJOR for breaking changes (renamed nodes, removed parameters).

Tags are pushed for every MINOR and MAJOR release. See [CHANGELOG.md](./CHANGELOG.md).

## Related projects

- **Memory variant:** [github.com/studiomeyer-io/n8n-templates](https://github.com/studiomeyer-io/n8n-templates)
- **Custom node:** [github.com/studiomeyer-io/n8n-nodes-studiomeyer-memory](https://github.com/studiomeyer-io/n8n-nodes-studiomeyer-memory)
- **Memory product:** [memory.studiomeyer.io](https://memory.studiomeyer.io)
- **Long-form tutorials:** [studiomeyer.io/blog](https://studiomeyer.io/blog) (filter: `n8n`)
- **Full ecosystem:** [ECOSYSTEM.md](./ECOSYSTEM.md)

## License

MIT, see [LICENSE](./LICENSE). Use these templates anywhere, including commercial deployments. Attribution appreciated, not required.

---

*Built by [StudioMeyer](https://studiomeyer.io) in Mallorca. Issues + ideas at [github.com/studiomeyer-io/n8n-workflows/issues](https://github.com/studiomeyer-io/n8n-workflows/issues).*
