# Changelog

All notable changes to this repository will be documented here. The format is loosely based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-05-02

Five new production templates. Repo grows from 5 to 10 hardened workflows, all sharing the same opt-in production-pattern foundation.

### Added

- **Template 06: [Calendly to CRM Sync](./templates/06-calendly-to-crm-sync/).** Calendly v2 webhook trigger with provider-specific HMAC signing (`Calendly-Webhook-Signature: t=<ts>,v1=<hmac>` over `<timestamp>.<rawBody>`, 5-min replay-window). Idempotency on `event.uri + invitee.uri`. Multi-CRM Switch (Pipedrive default, HubSpot, Salesforce) with explicit fallback output to `Error Fallback`. Lifecycle classification (booked / canceled / no_show). 20 nodes.
- **Template 07: [GitHub Issues Router](./templates/07-github-issues-to-tracker/).** GitHub `issues` webhook trigger with `X-Hub-Signature-256` HMAC. Idempotency on `X-GitHub-Delivery`. Multi-tracker Switch (Linear default GraphQL `issueCreate`, Jira REST `/rest/api/2/issue` with HTTP Basic auth, ClickUp REST `/list/{id}/task`). `Filter Event Type` returns `[]` for unforwarded actions to halt the branch cleanly. Followup comment back on the GitHub issue with the tracker URL. 21 nodes.
- **Template 08: [RSS to Multi-Channel Social](./templates/08-rss-to-multi-channel-social/).** Schedule trigger (every 30 min default). Multi-feed fan-out from `RSS_FEEDS` env. Lightweight RFC-compatible RSS / Atom parser without external XML lib. Per-feed-host rate limit (12 fetches / hour / host). 7-day idempotency on item guid (with `crypto`-hashed fallback key when guid missing). Multi-channel Switch (X v2 `/2/tweets` OAuth 1.0a, LinkedIn `/v2/ugcPosts`, Discord webhook). Pre-formatted per-channel post text. Per-channel error branches so one failing channel does not break the others. 19 nodes.
- **Template 09: [Calendar Conflict Detector](./templates/09-calendar-conflict-detector/).** Schedule trigger (daily 06:00 UTC default). Multi-calendar fan-out from `CALENDAR_IDS` env. Multi-provider Switch (Google Calendar v3 `events.list?singleEvents=true&orderBy=startTime`, Microsoft Graph `/users/{id}/calendarView`). Pair-wise interval-overlap algorithm across calendars (skips same-calendar pairs). Per-calendar rate limit + 24-hour idempotency on `sha256(eventA.id + eventB.id)`. Outlook timezone normalization with safe `Z` append (warns when a non-default `Prefer: outlook.timezone` header would cause silent local-time misinterpretation). 16 nodes.
- **Template 10: [CSV Bulk Validator](./templates/10-csv-bulk-validator/).** Webhook with `rawBody: true`. HMAC + replay-window protection (`x-csv-timestamp` + `x-csv-signature` over `<timestamp>.<rawBody>`, 5-min default, override via `CSV_UPLOAD_REPLAY_WINDOW_S`). Idempotency on `sha256(rawBody)`. Quote-aware RFC 4180 CSV parser with BOM strip + configurable delimiter + `MAX_BODY_BYTES` (5MB default) + `MAX_ROWS` (10k default) caps. Pre-compiled regex patterns from operator-controlled `VALIDATION_SCHEMA` env, with ReDoS heuristic (200-char cap + nested-quantifier refusal). Per-row sanitization (trim, control-char strip, type coercion, enum / pattern / min / max checks). Structured `{valid, invalid, summary}` response. `Parse CSV` error output wired to `Error Fallback` so parser-level errors return a graceful 200 with structured error log instead of an unhandled crash. 14 nodes.
- **Cover images via Flux 2 Max** for all 5 new templates (1216x640, navy + gold, $0.07 per image, $0.35 total).

### Quality gate

All 5 new templates structurally validated:

- 0 missing connection references
- 0 forbidden top-level keys
- 0 em-dashes in workflow.json or README.md or cover.md
- All 5 imported into n8n.studiomeyer.io v2.15.0 with HTTP 200, pre-activation-check passed (all node types recognized including `n8n-nodes-base.scheduleTrigger`, `n8n-nodes-base.webhook`, `n8n-nodes-base.code`, `n8n-nodes-base.switch`, `n8n-nodes-base.httpRequest`, `n8n-nodes-base.respondToWebhook`, `n8n-nodes-base.stickyNote`), then deleted to clean up the test workspace. Re-imported and re-deleted after the fix pass to verify the patches did not break import.
- 5 cover images generated and saved (Flux 2 Max).
- 3-agent code review parallel pass (Critic + Architect + Research) on the new five. Findings: 8 real bugs (5 P1 in workflow.json + 1 P1 in T08 README + 1 P1 in T08 X pricing claims + 1 P2 in T10 wiring), all fixed before commit. Findings list in the session memory.

### Fixed (in the same release as the additions, before commit)

- **T06: `Route by CRM` Switch had no fallback output.** Unknown `CRM_TARGET` values would silently dead-end. Added explicit `fallbackOutput: "extra"` so unmatched values flow into `Error Fallback`.
- **T06 + T07: Authorization header expressions missing `=` prefix.** Bare `{{ }}` in `headerParameters.value` is treated as a literal string by some n8n setups. Prefixed with `=` for explicit expression evaluation across HubSpot, Salesforce, Linear, ClickUp, and GitHub auth headers.
- **T07: `Filter Event Type` returned a sentinel item for unforwarded actions.** That sentinel flowed into `Normalize Payload` and produced blank tracker tickets. Now returns `[]` to halt the branch cleanly.
- **T08: README architecture diagram showed `Fetch RSS Feeds` before `Rate Limit (opt-in)`.** The actual workflow rate-limits before fetching. Diagram was reordered to match `List Feeds` -> `Rate Limit (opt-in)` -> `Fetch RSS Feed` -> `Parse RSS Items`.
- **T08: X (Twitter) Basic-tier pricing claim was outdated ($100/mo).** X doubled Basic to $200/mo in January 2025 and moved new signups to pay-per-use as the default in February 2026 (~$0.01 per post). Five README locations updated with the current 2026 reality.
- **T09: Outlook timezone normalization was broken for non-UTC timezones.** Original code only appended `Z` when `s.timeZone === 'UTC'` or empty; for `Prefer: outlook.timezone="Eastern Standard Time"` headers the dateTime string was passed unmodified to `new Date()` and parsed as local server time. Replaced with a strict `toUtcIsoStrict` helper that detects existing offset suffixes, appends `Z` for the calendarView default, and logs a warning when a non-UTC `timeZone` field is present without an explicit offset.
- **T10: `VALIDATION_SCHEMA` regex patterns lacked ReDoS protection.** Even though the schema is operator-controlled, a misconfigured pattern like `(a+)+$` could lock the n8n worker on a 10k-row file. Added a 200-char pattern cap + a heuristic that refuses common catastrophic-backtracking shapes before compile. Patterns are pre-compiled once per execution rather than per row.
- **T10: HMAC verification had no replay-window check.** Captured signed requests could be replayed indefinitely (different from T06 + T07 which both have replay windows). Added `x-csv-timestamp` header + 5-min default replay window (override via `CSV_UPLOAD_REPLAY_WINDOW_S`). Signed payload changed from raw body to `<timestamp>.<rawBody>` (Stripe-style).
- **T10: `Parse CSV` had no error output wired.** A malformed-body throw escaped as an unhandled workflow error instead of reaching the structured `Error Fallback`. Added `onError: continueErrorOutput` and the corresponding connection.

## [0.1.0] - 2026-05-02

Initial release. Five production n8n workflows with hardened patterns.

### Added

- **Repository scaffolding.** README, CONTRIBUTING, SECURITY, CODE_OF_CONDUCT, ECOSYSTEM, STATUS, PRODUCTION_CHECKLIST, MIT LICENSE. GitHub Actions CI (validate-workflows.yml + smoke-test-snippets.yml) with em-dash guard, forbidden top-level keys check, credential-leak scan, JSON validity check.
- **`templates/_TEMPLATE/` skeleton** at the v0.1.0 standard (8 mandatory README sections, opt-in production-pattern Code nodes, multi-provider Switch when LLM involved). Anyone copying the skeleton starts from a hardened baseline.
- **Template 01: [Form to CRM Lead Router](./templates/01-form-to-crm-lead-router/).** Form Webhook trigger + `LEAD_FORM_SIGNING_SECRET` HMAC. BANT-style scoring (Budget / Authority / Need / Timeline) via Code node. Multi-CRM Switch routes hot / warm / cold leads to Pipedrive (default), HubSpot, or Salesforce based on `CRM_TARGET` env var. All 4 production patterns wired. Cover image generated. 22 nodes.
- **Template 02: [Stripe Lifecycle to Slack](./templates/02-stripe-lifecycle-to-slack/).** Stripe webhook trigger with `Stripe-Signature` HMAC verification (timestamp + v1 hash, 5-minute replay window). Per-event-type Slack message templates for `checkout.session.completed`, `customer.subscription.{created,updated,deleted}`, `invoice.payment_failed`. Rate limit + idempotency on `event.id`. Slack incoming webhook with rich Block-Kit formatting. 20 nodes.
- **Template 03: [Uptime Monitor with Alerts](./templates/03-uptime-monitor-with-alerts/).** Schedule trigger (every 5 min default). Multi-target HTTP check via SplitInBatches loop over `MONITOR_TARGETS` env-var URLs. Retry-with-backoff (3 attempts). Status detection: HTTP 2xx = up, otherwise down. Idempotency on consecutive-failure dedup (do not spam alerts on persistent outages, only alert on state-change). Slack + Telegram alert branches. 18 nodes.
- **Template 04: [SSL Certificate Expiry Watcher](./templates/04-ssl-certificate-expiry-watcher/).** Schedule trigger (daily 09:00 UTC default). Multi-domain TLS check via `tls.connect` Code node. Days-until-expiry calculation. Three-tier alert: warning when <30 days, urgent when <14 days, critical when <7 days. Slack alert branch with severity-coded Block-Kit. 15 nodes.
- **Template 05: [Slack Channel Daily Digest](./templates/05-slack-channel-daily-digest/).** Schedule trigger (daily). Slack `conversations.history` fetch with cursor pagination. Multi-provider LLM summarization (OpenAI gpt-5.4-mini default, Anthropic claude-haiku-4-5 optional). Email summary via Brevo / SMTP + Slack-post into a digest channel. All 4 production patterns. 24 nodes.
- **Cover images via Flux 2 Max** for all 5 templates (1216x640, navy + gold, $0.07 per image, $0.35 total). Brand-consistent with the sister [n8n-templates](https://github.com/studiomeyer-io/n8n-templates) repo.
- **STATUS.md** as single source of truth per template (hardened / pending status, what is wired, what is pending).
- **PRODUCTION_CHECKLIST.md** with env vars, signing secrets, Redis snippet for clustered idempotency, reverse-proxy rate-limit pattern, smoke-test recipe, pre-launch checklist.
- **examples/** folder with sample payloads (form-submit, stripe-event, slack-message-event) for smoke-testing.

### Quality gate

All 5 new templates structurally validated:

- 0 missing connection references
- 0 forbidden top-level keys (`meta` / `staticData` / `versionId` / `id` / `tags`)
- 0 em-dashes in workflow.json or README.md or cover.md
- All 5 imported into n8n.studiomeyer.io v2.15.0 with HTTP 200, pre-activation-check passed (all node types recognized including `n8n-nodes-base.scheduleTrigger`, `n8n-nodes-base.webhook`, `n8n-nodes-base.code`, `n8n-nodes-base.switch`, `n8n-nodes-base.httpRequest`, `n8n-nodes-base.openAi`, `@n8n/n8n-nodes-langchain.anthropic`), then deleted to clean up the test workspace.
- 5 cover images generated and saved (Flux 2 Max).
- 3-agent code review (Critic + Architect + Research) on all 5 templates. AMBER findings fixed before commit.

### Memory variant cross-reference

Every template's README ends with a pointer to [studiomeyer-io/n8n-templates](https://github.com/studiomeyer-io/n8n-templates) for the cross-session-memory variant. Both repos share production-pattern foundation, the difference is whether StudioMeyer Memory is wired in.
