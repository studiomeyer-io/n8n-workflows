# Security Policy

## Supported versions

This repository ships n8n workflow templates, not application code. Each template is independently versioned through the `templates/NN-slug/` folder structure. The `main` branch is always the supported version. Older tags exist for reproducibility but receive no patches.

## Reporting a vulnerability

If you find a security issue in any of the workflows, the validation CI, or in how a template handles untrusted input (webhook payloads, API responses, customer data flowing through), report it via:

- Email: **hello@studiomeyer.io** with subject `[security] n8n-workflows`
- Encrypted: We respond to GPG-encrypted reports. Public key on request.

Please include:

1. Which template / file is affected.
2. Reproduction steps (or a redacted sample payload).
3. Why you believe it is a security issue (data leak, credential exposure, billing-spike vector, etc).
4. Whether you would like attribution in the fix commit.

We aim to acknowledge reports within 48 hours and to land a patch within 7 days for high-severity issues.

## Scope: what counts as a vulnerability

Things we treat as security issues:

- A template that leaks API keys, tokens, or customer data into logs, response bodies, or downstream services.
- A template that is vulnerable to header smuggling or signature forgery (HMAC bypass, replay attack).
- A template that hard-codes credentials, even in test fixtures.
- A template that calls a paid third-party API without a rate-limit, cost-cap, or idempotency guard, allowing an attacker to spike a builder's bill.
- The validate-workflows CI accepting workflow.json files that violate the repo security rules (real credentials, active=true at commit, etc).

Things that are not security issues but are still bug reports (open a normal `[bug]` issue):

- A template that does not work as documented.
- A template that fails on a new n8n version because of node-version drift.

## Coordinated disclosure

We ask reporters to wait for a fix before publishing details. If our patch is not landed within 30 days of a high-severity report, you are free to disclose publicly.

## Defense-in-depth context

The templates in this repo flow user input through:

1. n8n trigger node (webhook / schedule).
2. Optional opt-in production pattern Code nodes (HMAC verify, rate limit, idempotency).
3. Business logic Code nodes.
4. External API call (CRM, Slack, LLM, database).

Each layer has its own security profile. n8n itself is the perimeter the builder is responsible for. The opt-in pattern nodes provide defense-in-depth but are not a substitute for upstream protections (use a reverse-proxy rate limit too, store secrets in a vault, rotate signing keys).

If you find a security issue in a template that uses [StudioMeyer Memory](https://memory.studiomeyer.io) (none of the templates in this repo do, see [studiomeyer-io/n8n-templates](https://github.com/studiomeyer-io/n8n-templates) for those), report it at the n8n-templates repo or the same email.
