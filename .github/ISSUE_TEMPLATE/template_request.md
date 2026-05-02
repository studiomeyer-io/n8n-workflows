---
name: Template request
about: Suggest a new workflow template the repo should ship
title: "[template] "
labels: enhancement, template-request
assignees: ''
---

## Template idea (one sentence)

What should it do? Who is the target builder?

## Trigger

What kicks the workflow off (webhook, schedule, polling, chat trigger)?

## Memory dependency

Does it need cross-session memory? If yes, please open the issue against [studiomeyer-io/n8n-templates](https://github.com/studiomeyer-io/n8n-templates) instead. This repo is intentionally memory-free.

## LLM call

Provider-agnostic? Or specific to one provider? If LLM is involved at all, the multi-provider Switch pattern is mandatory.

## Production patterns applicable

Which of the four patterns are needed?

- [ ] HMAC webhook verification (only if trigger is a public webhook with a provider-side signing secret)
- [ ] Idempotency (any retry-prone trigger)
- [ ] Rate limit (any public webhook)
- [ ] Error branches (always)

## Distribution value

Why would a builder feature this on Reddit, dev.to, or LinkedIn? What is the search query they would find it under?

## Existing alternatives

Anything similar already on n8n.io/workflows or in this repo? How does this differ?
