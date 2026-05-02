# StudioMeyer Ecosystem

`n8n-workflows` is part of the StudioMeyer open source toolkit. Here is everything we build and maintain in the same family.

## n8n Integration

| Project | Description | Install |
|---------|-------------|---------|
| **[n8n-workflows](https://github.com/studiomeyer-io/n8n-workflows)** *(this repo)* | Production n8n workflows with hardened patterns. No memory required. 10 templates: CRM router, Stripe, uptime, SSL, Slack digest, Calendly, GitHub issues, RSS, calendar conflicts, CSV validator. | clone + import |
| **[n8n-templates](https://github.com/studiomeyer-io/n8n-templates)** | Memory-backed n8n workflows. Voice agents, customer support, personal assistants, restaurant bots. Same production patterns, plus StudioMeyer Memory for cross-session context. | clone + import |
| **[n8n-nodes-studiomeyer-memory](https://github.com/studiomeyer-io/n8n-nodes-studiomeyer-memory)** | Official n8n community node for StudioMeyer Memory. 16 operations across Memory, Entity, Session, Insight resources. | `npm install n8n-nodes-studiomeyer-memory` |

## MCP Server Products (Hosted)

| Product | Tools | What it does | Link |
|---------|-------|-------------|------|
| **StudioMeyer Memory** | 56 | Persistent AI memory with knowledge graph, semantic search, multi-agent support, 3D visualizations | [memory.studiomeyer.io](https://memory.studiomeyer.io) |
| **StudioMeyer CRM** | 33 | Headless CRM (contacts, companies, deals, pipeline, health scores, Stripe sync) | [crm.studiomeyer.io](https://crm.studiomeyer.io) |
| **StudioMeyer GEO** | 24 | AI visibility monitoring across 8 LLM platforms (ChatGPT, Gemini, Perplexity, Claude, Grok, DeepSeek, Meta AI, Copilot) | [geo.studiomeyer.io](https://geo.studiomeyer.io) |
| **MCP Crew** | 10 | 13 expert personas (CEO, CFO, CMO, CTO, PM, Analyst, Support, Creative, plus 5 Pro tiers) with domain frameworks | [crew.studiomeyer.io](https://crew.studiomeyer.io) |

All MCP products use OAuth 2.1 + Magic Link authentication. Free tiers available. EU Frankfurt hosting.

## Open Source Tools

| Project | Description | Install |
|---------|-------------|---------|
| **[AI Shield](https://github.com/studiomeyer-io/ai-shield)** | LLM security: prompt injection, PII, cost tracking, tool policies, audit logging | `npm install ai-shield-core` |
| **[Darwin Agents](https://github.com/studiomeyer-io/darwin-agents)** | Self-evolving AI agents with A/B testing and safety gates | `npm install darwin-agents` |
| **[Agent Fleet](https://github.com/studiomeyer-io/agent-fleet)** | Multi-agent orchestration for Claude Code CLI | clone + `npm install` |
| **[MCP Personal Suite](https://github.com/studiomeyer-io/mcp-personal-suite)** | 49 personal-productivity tools across mail, calendar, files, tasks, and notes | `npx mcp-personal-suite` |
| **[MCP Video](https://github.com/studiomeyer-io/mcp-video)** | Cinema-grade video production via MCP (FFmpeg + Playwright) | `npx mcp-video` |
| **[Local Memory MCP](https://github.com/studiomeyer-io/local-memory-mcp)** | Self-hosted SQLite-backed Memory for builders who want zero-cloud | `npm install local-memory-mcp` |

## Claude Code Plugin Marketplace

Install all four MCP products plus the n8n custom node as Claude Code plugins with one command:

```bash
/plugin marketplace add studiomeyer-io/studiomeyer-marketplace
```

## Where this repo fits

The flow we expect a builder to take:

1. They search for "n8n stripe slack signed webhook" or "n8n uptime monitor with alerts" or "n8n form to multi-crm".
2. They land on this repo. They import the workflow.json into their n8n instance.
3. They flip the production pattern env vars on for their stack (HMAC, rate limit, idempotency).
4. The workflow runs in production with proper signature verification, retry-safe, error-handled.
5. If they need cross-session memory ("the support agent should remember last week's ticket"), they look at the sister [n8n-templates](https://github.com/studiomeyer-io/n8n-templates) repo.

Each step adds value. Each step is independently reversible. The workflows are MIT, the patterns are documented end-to-end, the Memory backend (if you go that route) has its own discovery doc and its own SDK.

## License

Every project in this ecosystem ships under [MIT](LICENSE) unless explicitly stated otherwise. Use them in commercial deployments without permission. Attribution appreciated but not required.

## Contact

- General: [hello@studiomeyer.io](mailto:hello@studiomeyer.io)
- Studio: [studiomeyer.io](https://studiomeyer.io)
- Built in Mallorca.
