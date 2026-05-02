---
name: Bug report
about: Something in a template does not work as documented
title: "[bug] "
labels: bug
assignees: ''
---

## Which template

`templates/NN-slug/`

## What happened

A clear, plain-text description. Include the n8n version and (where applicable) the LLM provider you picked.

## Expected behavior

What should have happened instead.

## Reproduction

Numbered steps. If the issue is in `workflow.json`, paste the exact node parameters that misbehave (with credentials redacted).

```
1. Imported workflow.json into n8n 1.x
2. Set Provider to anthropic
3. Triggered webhook with payload {...}
4. Got error: ...
```

## Logs

Paste the n8n execution log around the failing node. Redact API keys, tokens, and customer data.

## Environment

- n8n version:
- Provider used (OpenAI / Anthropic / Stripe / Pipedrive / Slack / other):
- Hosting (Cloud / self-hosted Docker):
- Production-pattern env vars enabled (`WEBHOOK_INTEGRITY_CHECK_ENABLED` / `RATE_LIMIT_ENABLED` / `IDEMPOTENCY_ENABLED`):
