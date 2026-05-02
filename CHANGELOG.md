# Changelog

All notable changes to this repository will be documented here. The format is loosely based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2026-05-02

Five more production templates. Repo grows from 10 to 15 hardened workflows, all sharing the same opt-in production-pattern foundation. The 10-item Tier-4 backlog is now complete.

### Added

- **Template 11: [Email to Notion](./templates/11-email-to-notion/).** IMAP poll trigger (default 5 min). Optional sender-domain + subject-keyword filter via `EMAIL_FROM_WHITELIST` + `EMAIL_SUBJECT_INCLUDE` env. Idempotency on `sha256(message_id)`. Rate limit on the Notion write call. HTML-stripping + snippet cap at 1800 chars (Notion rich_text per-segment soft-limit). Notion API v1 page-create with structured properties (Subject, From, Snippet, ReceivedAt, Attachments, MessageId). Slack-on-Notion-failure error branch. 13 nodes.
- **Template 12: [Postgres to Google Sheets Sync](./templates/12-postgres-to-sheets-sync/).** Schedule trigger (daily 06:00 UTC default). Persistent high-water-mark via `$getWorkflowStaticData` (seeded by `PG_SYNC_HWM_INITIAL`). Postgres `executeQuery` with `$1` placeholder for the HWM. 24-hour idempotency window on row primary key. Hard `MAX_ROWS_PER_RUN` cap (default 5000) defends against runaway queries. Transform via `PG_SYNC_COLUMN_ORDER` env. Google Sheets API v4 append. HWM advances only on the success path so a failed run does not skip rows. Stage-classified error branch. 14 nodes.
- **Template 13: [Webhook Audit Trail](./templates/13-webhook-audit-trail/).** Generic signed-event ingest endpoint. HMAC + replay-window verify (`x-audit-signature` + `x-audit-timestamp` over `<timestamp>.<rawBody>`, 5-min default override via `AUDIT_REPLAY_WINDOW_S`). Per-IP rate limit (default 60 / 5 min override via `AUDIT_RATE_LIMIT_PER_IP`). Idempotency on `x-request-id` or hashed body. Postgres `audit_log` insert with hash chain (`prev_hash` + `payload_hash` + metadata -> `row_hash`) so tampering is detectable. Slack alert categorized by error class (auth, capacity, database). Status-coded responses (401 / 413 / 429 / 500). 14 nodes.
- **Template 14: [Telegram Translator Bot](./templates/14-telegram-translator-bot/).** Telegram Trigger with `secret_token` validation enforced by the node when `TELEGRAM_WEBHOOK_SECRET` is set in env. Filter non-text + bot-self messages + bot commands. Per user_id rate limit. 5-min idempotency on Telegram `update_id`. Multi-provider Switch (OpenAI gpt-5.4-mini default, Anthropic claude-haiku-4-5 optional) with `fallbackOutput: extra` for typo defense. LLM Fallback Reply with `isLlmError` discriminator preventing system-prompt JSON-stringify leak (router-fallback case discriminated from real LLM error). Telegram Reply with onError -> fallback path. 15 nodes.
- **Template 15: [YouTube Channel to Notion](./templates/15-youtube-channel-to-notion/).** Schedule trigger (daily 04:00 UTC default). Multi-channel fan-out from `YOUTUBE_CHANNEL_IDS` env (cap 50). Public YouTube RSS fetch (no API key required for the basic flow). Lightweight regex-based RSS / Atom parser (no external XML lib). 90-day persistent idempotency on `videoId`. `MAX_VIDEOS_PER_CHANNEL_PER_RUN` cap (default 10) for first-run defense. Optional LLM summary toggle with multi-provider Switch. Notion API v1 page-create with Title, Channel, Url, PublishedAt, Summary, VideoId. Stage-classified error branch. 18 nodes.
- **Cover images via Flux 2 Max** for T11-T14 (1216x640, navy + gold, $0.07 each). T15 cover via gpt-image-2 free tier ($0.009) due to Flux credit exhaustion at this build. Total cover spend $0.289.

### Changed

- **Notion-Version header bumped** from `2022-06-28` to `2025-09-03` (SDK-default conservative) in T11 + T15. The 2022-06-28 string still works (Notion is backward-compatible across version pins) but was four major versions behind. The `2025-09-03` value matches the official Notion JavaScript SDK default and is current as of May 2026.

### Fixed (in the same release as the additions, before commit)

The 3-agent Cold-Review-Sweep (Critic + Architect + Research) on the five new templates produced 8 unique findings (with 3 overlaps between Critic and Architect). All fixed before commit:

- **T13: Hash chain advanced before DB commit (Critic P2-2 + Architect F2 HIGH).** Build Audit Row's `data.lastRowHash = rowHash` ran in the in-memory static-data BEFORE Postgres Insert succeeded. On a DB failure the chain pointer moved forward to a hash for a row never written. Plus the static-data was lost on n8n restart, so the first row after restart silently re-bound to genesis. Both fixed by moving the chain compute into the SQL itself: the Postgres Insert is now a single atomic statement using `WITH last AS (SELECT row_hash FROM audit_log ORDER BY id DESC LIMIT 1 FOR UPDATE), seed AS (...) INSERT ... SELECT ... encode(digest(json_build_object(...)::text, 'sha256'), 'hex') ... RETURNING id, prev_hash, row_hash;`. Restart-resilient (state in DB) and race-safe (FOR UPDATE locks the predecessor inside the same transaction).
- **T13: Idempotency Check missing onError (Critic P2-1).** The Code node had no `onError: continueErrorOutput` and no error-output connection to Error Fallback. An unexpected static-data corruption escaped as an unhandled n8n exception. Fixed by adding `onError: continueErrorOutput` and wiring the error pin to Error Fallback, matching the Verify Webhook + Rate Limit pattern.
- **T13: Parallel-execution race on `prev_hash` (Architect F3 HIGH).** Two concurrent inserts could read the same `prev_hash` from in-memory state and produce a chain fork. Implicitly fixed by the SQL refactor above (FOR UPDATE serialization).
- **T14: Sticky Note claimed Slack alert that did not exist (Critic P2).** The Production Patterns sticky said "Reply-send failure -> structured log + Slack alert" but no Error Fallback or Slack Alert node existed. Fixed by adding both nodes (Error Fallback Code node + Slack Alert HTTP node bound to `SLACK_OPS_WEBHOOK`) and fan-out wiring on the Telegram Reply error pin: error -> [LLM Fallback Reply (user-facing) AND Error Fallback (ops-facing)] -> Slack Alert. Sticky note rewritten to match.
- **T14: Stale "Build Audit Row" reference in README Hard compatibility floor (Critic P3 + Architect F4 MEDIUM).** Copy-paste artifact from T13's README. T14 has no Build Audit Row node. Fixed to "the `Idempotency Check (opt-in)` Code node uses `require('crypto')`".
- **T15: Index-based metadata lookup breaks on partial LLM failure (Critic P1 + Architect F6 LOW).** Normalize Video Item used `items.indexOf(item)` to look up upstream video metadata. When OpenAI/Anthropic erred on a subset of items, the error batch starts indexing at 0 in Normalize, so `upstream[0]` was always returned regardless of which video failed, writing wrong title/url/videoId to Notion for every LLM-failed item. Fixed with three-tier resolution: pairedItem (n8n's stable cross-branch tracking) -> in-place $json.videoId (no-summary path) -> array-index fallback. Plus a fail-safe that drops items with `metadata-lookup-failed` rather than writing garbage to Notion.
- **T11 + T15: Notion-Version header outdated (Research finding).** `2022-06-28` is four major versions behind. Bumped to `2025-09-03` (the official Notion JavaScript SDK default, conservative-current). Documented in Tech stack matrix.
- **All 5: Architecture-diagram ASCII-vs-box-drawing drift (Architect F1 MEDIUM).** Diagrams used plain `|` and `v` while T01-T10 use `│` and `▼`. Batch-fixed across all five new templates.

### Quality gate

All 5 new templates structurally validated, twice (post-build + post-fix):

- 0 missing connection references
- 0 forbidden top-level keys (`meta` / `staticData` / `versionId` / `id` / `tags`)
- 0 em-dashes in workflow.json or README.md or cover.md
- 0 credential leaks
- 0 sensitivity matches (internal paths, internal domains, session numbers)
- All 5 imported into n8n.studiomeyer.io v2.15.0 with HTTP 200, pre-activation-check passed (all node types recognized including `n8n-nodes-base.scheduleTrigger`, `n8n-nodes-base.webhook`, `n8n-nodes-base.code`, `n8n-nodes-base.switch`, `n8n-nodes-base.httpRequest`, `n8n-nodes-base.respondToWebhook`, `n8n-nodes-base.stickyNote`, `n8n-nodes-base.emailReadImap`, `n8n-nodes-base.postgres`, `n8n-nodes-base.telegramTrigger`, `n8n-nodes-base.noOp`), then deleted to clean up the test workspace. Re-imported and re-deleted after the fix pass to verify the patches did not break import.
- 5 cover images generated and saved.
- 3-agent code review parallel pass (Critic + Architect + Research). All 8 unique findings fixed before commit (full list above). Findings list in the session memory.

### Cumulative repo-wide audit (T01-T15)

The repo-wide audit at v0.3.0 release confirms:

- All 15 workflow.json files structurally valid (no missing refs, no forbidden keys, no `active=true`, no `pinData`)
- 0 em-dashes in any committable file (templates/, examples/, root markdown, .github CI)
- 0 credential leaks across all 15 workflow.json
- 0 sensitivity matches in any committable file (filename patterns, internal paths, internal domains, session numbers)

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
