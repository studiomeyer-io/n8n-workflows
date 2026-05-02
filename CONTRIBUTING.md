# Contributing

Thanks for considering a contribution. The bar for new templates is high. Each template has to ship the production patterns this repo is known for.

## What we accept

A template is a strong candidate when it:

- Solves a concrete workflow problem that an n8n builder has searched for at least once.
- Ships the four production patterns (HMAC verify, rate limit, idempotency, error branch) where applicable.
- Has a clear primary trigger (webhook, schedule) and a clear primary outcome (notify, sync, log).
- Works end-to-end after the user fills in their credentials. No "TODO finish this" branches.

A template is **not** a good fit when it:

- Wraps a single API call without orchestration.
- Requires a paid third-party service most users will not have (exotic CRM with no free tier, niche analytics platform).
- Replicates something already in this repo with cosmetic changes.
- Is memory-dependent. Memory templates belong in [studiomeyer-io/n8n-templates](https://github.com/studiomeyer-io/n8n-templates).

## Folder layout

```
templates/NN-descriptive-slug/
├── workflow.json     # exported from n8n, hand-cleaned (see below)
├── README.md         # mandatory (see below)
└── cover.md          # cover-image spec
```

The slug starts with a two-digit prefix matching the position in the README templates table.

## workflow.json checklist

Before committing:

1. **Strip credentials.** Open the JSON and remove any `credentials` blocks that point to a real credential ID. The user attaches their own credentials after import.
2. **Strip versionIds + ids.** Set every node `id` to a stable string (e.g. `"stripe-1"`, `"stripe-2"`) instead of a UUID. n8n regenerates them on import.
3. **Remove `pinData`.** Test data should not ship.
4. **Strip forbidden top-level keys.** The n8n Public API rejects `meta`, `staticData`, `versionId`, `id`, `tags` on POST `/api/v1/workflows`. CI blocks these.
5. **Set `active: false`.** Imports should never go live silently.
6. **Sanitize webhook paths.** Replace any random path segments with descriptive defaults (e.g. `stripe-webhook`).
7. **Add `>> SET ME <<` markers.** Every value the user must change (webhook URL, model name, tokens) must be obvious. Use either a sticky note or a `// SET ME:` comment in code nodes.
8. **No em-dashes.** CI blocks em-dashes (U+2014) in workflow.json and README. Use comma, period, or parenthesis.
9. **Test the import path yourself.** Import the JSON into a fresh n8n instance, fill in placeholders, and run a real test transaction.

## README.md template

Use `templates/_TEMPLATE/README.md` as the starting point. The mandatory sections (in order):

1. StudioMeyer MCP Stack banner
2. Title + cover image
3. What this does (two paragraphs)
4. Architecture (ASCII diagram)
5. Setup (numbered steps)
6. Multi-provider switch (if LLM is involved)
7. Extending (3-4 concrete ideas)
8. Cost notes (table)
9. Common gotchas (3-5 items)
10. Production patterns (the 4 patterns that ship)
11. Hard compatibility floor (n8n version + CVE)
12. Credentials checklist
13. Related templates
14. Footer

If a template has no LLM, the multi-provider switch section is skipped and a one-line note says so. Everything else is mandatory.

## Cover image

Each template needs a cover image. Recommended size: 1216x640, dark navy + gold (suite-consistent), three icons (trigger source, key node, output) and the template title in bold. We use Flux 2 Max for generation (~$0.07 per image). The prompt and resulting URL go into `cover.md`.

## Commit + PR

- One template per PR.
- Branch name `template/NN-slug`.
- Commit message: `feat(templates): add NN <title>`.
- PR description must include a screenshot of a successful test run from your own n8n instance.

## Review

A maintainer will:

1. Import your `workflow.json` into a clean n8n instance.
2. Verify all four production patterns work as documented (toggle env vars, watch nodes activate).
3. Read the README for clarity.

If everything checks out, we merge, tag the next minor version, and submit the template to n8n.io within a week.

## 3-agent quality gate

Substantial PRs (new templates, breaking changes) go through a 3-agent code review (Critic + Architect + Research) before merge. This is on the maintainer side, you do not need to run it. Findings get addressed inline before the PR is merged.

## License

By contributing you agree your work is released under the [MIT License](./LICENSE).
