# Changelog

All notable changes to this repository will be documented here. The format is loosely based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
