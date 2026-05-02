# Pull request

## What this PR does

One paragraph. New template? Fix in existing template? Repo-wide infrastructure change?

## Quality check

Confirm the change passes the internal quality checklist:

- [ ] All 14 README sections present and in order (if README touched). See [CONTRIBUTING.md](../CONTRIBUTING.md).
- [ ] No em-dashes (the `U+2014` character) in any markdown or workflow.json. CI runs the validate-workflows GitHub Action which fails on any em-dash match in `templates/`, examples, or root markdown.
- [ ] `workflow.json` validates: missing refs NONE, no forbidden top-level keys (`meta`, `staticData`, `versionId`, `id`, `tags`), `pinData` empty, `active` false or omitted.
- [ ] No real credentials, secrets, or test pinData committed (CI scans for literal API keys, Bearer tokens, JWTs).
- [ ] All `>> SET ME <<` markers visible as Sticky Notes.
- [ ] Multi-Provider pattern in place if an LLM call exists (`Set Provider` + `Route by Provider` Switch + `Normalize LLM Output` Code node).
- [ ] All four production patterns wired where applicable: HMAC verify (opt-in), Rate Limit (opt-in), Idempotency (opt-in), Error Branch (always on).
- [ ] Cover image generated and committed (`cover.png`, 1216x640, navy + gold, Flux 2 Max).
- [ ] Smoke-tested in a real n8n instance (paste execution-id below).
- [ ] Cross-links to related templates work.
- [ ] Top-level CHANGELOG.md updated.
- [ ] Memory-free. If the workflow needs cross-session memory, the PR belongs at [studiomeyer-io/n8n-templates](https://github.com/studiomeyer-io/n8n-templates).

## Smoke-test evidence

n8n execution-id: `<paste>`
n8n version: `<paste>`

## Screenshots / GIFs

If the change is visual (cover image, sticky-note layout), include before/after screenshots.

## Related issues

Closes #
References #
