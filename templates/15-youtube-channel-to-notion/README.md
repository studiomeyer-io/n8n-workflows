<!-- studiomeyer-mcp-stack-banner:start -->
> **Part of the [StudioMeyer MCP Stack](https://studiomeyer.io)**, Built in Mallorca · ⭐ if you use it
<!-- studiomeyer-mcp-stack-banner:end -->

# YouTube Channel to Notion

> Schedule trigger watches a list of YouTube channels via public RSS, dedupes by videoId, optionally summarizes each new video via OpenAI / Anthropic, writes one Notion database row per video. No YouTube Data API key required for the basic flow.

![Cover](./cover.png)

## What this does

The Schedule trigger fires daily 04:00 UTC. The workflow reads `YOUTUBE_CHANNEL_IDS` (comma-separated list of `UC...` IDs), fetches the public RSS feed at `https://www.youtube.com/feeds/videos.xml?channel_id=...` for each channel, parses the XML with a small built-in regex parser, dedupes against a 90-day persistent set of seen `videoId`s, optionally calls OpenAI / Anthropic for a 2-3 sentence summary of title + description, then writes one Notion page per new video into the configured database.

The result is an auto-archive of every channel you watch, queryable in Notion, optionally with AI-generated TL;DRs. Useful for research workflows ("which YouTube videos discussed n8n templates this week") and content-sourcing teams that need a structured backlog of new uploads.

## Architecture

```
[Schedule (Daily 04:00 UTC)]
    │
    ▼
[List Channels]                      YOUTUBE_CHANNEL_IDS env, one item per channel
    │
    ▼
[Rate Limit (opt-in)]                30 RSS fetches / hour / host
    │
    ▼
[Fetch YouTube RSS]                  public RSS, no API key, onError → Error Fallback
    │
    ▼
[Parse RSS]                          regex-based XML parsing, no external lib
    │
    ▼
[Idempotency Check (opt-in)]         90-day persistent map of seen videoIds, MAX_VIDEOS_PER_CHANNEL_PER_RUN cap
    │
    ▼
[Build Summary Prompt]               LLM_SUMMARY_ENABLED=1 toggles LLM, otherwise no-op
    │
    ▼
[Route by Provider]                  skipped + no-summary + openai + anthropic + fallback
    |              |              |              |
   skipped      no-summary       openai       anthropic
    (drop)         |              |              |
                   v              v              v
            [Normalize Video Item]   [OpenAI / Anthropic Summarize]
                   |                            |
                   |  onError → Normalize back into pipeline
                   v                            v
            [Notion Create Page]                |
                   |                            |
                onError → Error Fallback → Slack Alert
                   ▼
            [Done]
```

## Setup

1. **Import this workflow** (workflow.json in this folder).
2. **Find the channel IDs you want to watch.** Open a channel page on YouTube, right-click View Source, ctrl-F `channel_id`. The value is a string like `UCxxxxxxxxxxxxxxxxxxxx`. Or use third-party tools like https://commentpicker.com/youtube-channel-id.php.
3. **Set `YOUTUBE_CHANNEL_IDS`** to a comma-separated list. Hard cap of 50 channels per run.
4. **Create a Notion Internal Integration.** notion.so/my-integrations, copy the secret token. Set `NOTION_API_TOKEN` env.
5. **Create a Notion database** with these columns: `Title` (Title), `Channel` (Text), `Url` (URL), `PublishedAt` (Date), `Summary` (Text), `VideoId` (Text). Copy the database ID. Set `NOTION_DATABASE_ID` env.
6. **Share the database with your integration** (top-right Share menu).
7. **Optional LLM summary.** Set `LLM_SUMMARY_ENABLED=1`, `LLM_PROVIDER=openai` (default) or `anthropic`, add the matching credential.
8. **Optional `SLACK_OPS_WEBHOOK`** for error alerts.
9. **Production patterns.** Set `RATE_LIMIT_ENABLED=1` and `IDEMPOTENCY_ENABLED=1`.
10. **Test.** Manually run the workflow. The first run picks up the latest 10 videos per channel (capped via `MAX_VIDEOS_PER_CHANNEL_PER_RUN`). Subsequent runs only see new uploads since the last run.

## Multi-provider switch

The optional LLM summary uses the same multi-provider Switch pattern as templates 05 and 14: `Build Summary Prompt` sets `provider` based on `LLM_PROVIDER` env, `Route by Provider` Switch routes to the matching HTTP node, both branches converge in `Normalize Video Item`. The Switch has explicit rules for `skipped`, `no-summary`, `openai`, `anthropic`, plus a fallback for any other value (typo in `LLM_PROVIDER`).

To add a third provider (Gemini), copy the OpenAI HTTP node, change URL + credentials, add a Switch rule, connect to `Normalize Video Item`. Update `Normalize Video Item` to recognize Gemini's response shape (`candidates[0].content.parts[0].text`).

## Extending

**Auto-fetch transcripts.** YouTube does not expose transcripts via the public RSS, but the Data API v3 does (`captions.list` + `captions.download`). Add an HTTP node after `Idempotency Check` that fetches the auto-caption track. Cost: $1 / 1000 quota units, the captions endpoints cost ~50 quota each. Useful for transcript-driven Notion search across the archive.

**Filter by keyword.** Insert a Code node between `Parse RSS` and `Idempotency Check` that drops items whose title or description does not match a `YOUTUBE_KEYWORD_FILTER` regex. Useful for a research feed where only AI / engineering / specific-topic videos should land in Notion.

**Cross-post new videos.** After `Notion Create Page`, fork into a Discord webhook or LinkedIn post to push every new video to your community channels. Pair with the [08 - RSS to Multi-Channel Social](../08-rss-to-multi-channel-social/) for a more general fan-out.

**Channel-grouped Notion subpages.** Edit `Notion Create Page` to use `parent: { type: 'page_id', page_id: <channel-page-id> }` instead of a flat database. The integration must be shared with each parent page. Useful when you want a folder per channel.

**Live-stream detection.** YouTube RSS marks live streams via `yt:videoId` plus a `<media:status state="live">` element. Edit `Parse RSS` to extract that and add an `IsLive` boolean to the Notion row. Useful for live-event aggregation feeds.

## Cost notes

Per execution (one daily run with 10 channels and 5 new videos average):

| Component | Cost (Stand 2026-05) | Per-execution cost |
|---|---|---|
| **n8n** (self-hosted) | free | $0 |
| **n8n Cloud** | from $20/mo | included |
| **YouTube RSS fetch** | free (public RSS, no API key) | $0 |
| **Notion API** | free up to 3 calls / sec / integration | $0 |
| **OpenAI gpt-5.4-mini** (when LLM_SUMMARY_ENABLED=1) | $0.75 / 1M input + $4.50 / 1M output | ~$0.0005 / video |
| **Anthropic claude-haiku-4-5** (when LLM_SUMMARY_ENABLED=1) | $1.00 / 1M input + $5.00 / 1M output | ~$0.0008 / video |

Per-execution cost without LLM summary: **$0**.
Per-execution cost with LLM summary, 50 new videos / day total: **~$0.025 / day** (~$0.75 / month).

**Worked example at 50 channels and 250 new videos / month with OpenAI summary:**

| Stack | Cost | Total /mo |
|---|---|---|
| n8n self-hosted, OpenAI summary | $0 base + ~$0.13 LLM | ~$0.13 / mo |
| n8n Cloud + OpenAI summary | $20 base + ~$0.13 LLM | ~$20 / mo |

The LLM cap (`max_tokens: 200`) bounds runaway summaries.

## Common gotchas

- **YouTube RSS only returns the latest 15 videos per channel.** If a channel uploads more than 15 videos between runs, you miss the older ones. Mitigation for high-volume channels: run more frequently (every 12 hours instead of 24) OR switch to YouTube Data API v3 with `playlistItems.list` for the channel's uploads playlist.
- **Channel ID is not the channel handle (@username).** Many channels show `@username` in the URL but the RSS feed needs `UC...`. The username-to-channel-id lookup needs the YouTube Data API or third-party tools.
- **First run grabs the latest 10 videos per channel.** This template caps at `MAX_VIDEOS_PER_CHANNEL_PER_RUN=10` so the first import does not flood Notion with hundreds of pages. After the first run, only new uploads land.
- **`videoId` dedup persists for 90 days then evicts.** A video older than 90 days that suddenly comes back into the feed (rare, but YouTube does shift content) would be re-imported. Adjust `KEEP_DAYS` in `Idempotency Check` if you need a longer window.
- **Notion rich-text per-segment soft-limit is ~2000 chars.** This workflow caps `description` and `summary` at 1800 / 1000 chars. If your LLM produces a longer summary, it gets truncated.
- **`Notion API 404` on the first run.** Almost always means the database is not shared with your integration. Open the database, click Share, add the integration. Re-run.
- **Workflow restart loses the seen-videos state.** The default idempotency check uses `$getWorkflowStaticData('global')` which is per-workflow-instance. After a restart, the first run can re-import the latest 10 videos per channel because the seen-set is empty. Mitigation: persist seen-videos to a 1-row Postgres / Redis config OR accept the duplicate-on-restart cost (rare).
- **YouTube can rate-limit RSS fetches if you watch hundreds of channels in tight loops.** Their public RSS is not a documented API, no documented rate limit, but observed limits around 30 requests / minute per IP. The opt-in rate limiter caps at 30 / hour as defense.
- **n8n core HTTP request body shape.** The HTTP Request node's body parameter expects a string, not a JSON object. Wrap with `JSON.stringify({...})` in expressions.
- **n8n error syntax.** Inline error pin uses `{{ $json.error.message }}`. Separate Error Trigger Workflow uses `{{ $json.execution.error.message }}` + `{{ $json.workflow.name }}`. Often-quoted `{{ $error.message }}` does not exist.

## Production patterns

Three opt-in patterns ship in `workflow.json` as actual nodes plus one always-on error branch.

**Idempotency** (opt-in, `IDEMPOTENCY_ENABLED=1`). The `Idempotency Check` Code node holds a 90-day persistent map of seen `videoId` values via `$getWorkflowStaticData('global')`. The same video, fetched twice across runs, lands in Notion once. Eviction caps the map at 50000 entries. For clustered n8n, swap to Redis with a 90-day TTL OR a Postgres `seen_videos` table queried before each insert.

**Rate limiting** (opt-in, `RATE_LIMIT_ENABLED=1`). Per-host sliding window, 30 RSS fetches / hour. Map bounded at 5000 entries with eviction. YouTube does not publish a documented rate limit but observed limits around 30 / minute / IP, the opt-in cap is far below that for safety.

**Hard cap on videos per run per channel** (`MAX_VIDEOS_PER_CHANNEL_PER_RUN`, default 10). Defends against the first-run scenario where a brand-new workflow with 50 channels + 15 videos per channel would write 750 Notion rows in one run. The cap silently slices to the first 10 per channel. Subsequent runs pick up the rest.

**Multi-provider Switch with router-fallback discrimination** (always on, opt-in via `LLM_SUMMARY_ENABLED=1`). The `Route by Provider` Switch has explicit rules for skipped, no-summary, openai, anthropic, plus a fallback for unknown provider values. The fallback path routes to `Normalize Video Item` directly so a typo in `LLM_PROVIDER` does not break the workflow, just skips the summary for that batch.

**Error branches** (always on). `Fetch YouTube RSS`, both LLM HTTP nodes, and `Notion Create Page` all have `On Error: Continue (Using Error Output)` enabled. Errors land at `Error Fallback` which classifies the stage (rss-fetch, openai, anthropic, notion) and triggers `Slack Alert` if `SLACK_OPS_WEBHOOK` is set.

There is no HMAC node in this template. Schedule trigger, server-internal.

## Hard compatibility floor

**Minimum n8n version with CVE-2026-27493 fix:** >= 2.9.3 (stable channel) / >= 2.10.1 (latest / beta channel) / >= 1.123.22 (1.x LTS). CVE-2026-27493 is an unauthenticated RCE in Form nodes (CVSS 9.5). This template does not use Form nodes (uses Schedule + RSS + Notion), but you should still upgrade for general security.

**Self-hosted Node builtins:** the Code nodes do not currently require any builtins. Set `NODE_FUNCTION_ALLOW_BUILTIN=crypto` if you extend the template with hash-based dedup.

## Tech stack matrix

| Component | Version | Cost | Free tier | Required when |
|---|---|---|---|---|
| n8n | >= 2.10.1 (CVE-2026-27493 floor) | self-hosted free / Cloud $20/mo | n8n Cloud trial | always |
| YouTube public RSS | latest | free | no API key required | always |
| Notion | API v2 (`Notion-Version: 2025-09-03`, SDK-default conservative) | free | always | always |
| OpenAI | gpt-5.4-mini | $0.75 / 1M input + $4.50 / 1M output | $5 trial credit | LLM_SUMMARY_ENABLED=1 + provider=openai |
| Anthropic | claude-haiku-4-5 | $1.00 / 1M input + $5.00 / 1M output | $5 trial credit | LLM_SUMMARY_ENABLED=1 + provider=anthropic |

## Credentials checklist

Before activation, create these credentials in n8n:

- [ ] **Notion API token** in `NOTION_API_TOKEN` env.
- [ ] **Notion database ID** in `NOTION_DATABASE_ID` env.
- [ ] **Database shared** with the Notion integration.
- [ ] **`YOUTUBE_CHANNEL_IDS`** comma-separated.
- [ ] **OpenAI API** OR **Anthropic API** credential (only when `LLM_SUMMARY_ENABLED=1`).
- [ ] **Slack incoming webhook URL** in `SLACK_OPS_WEBHOOK` env (optional).

## Need cross-session memory?

This template is a stateless watch-and-archive workflow. If you want to track which videos a person has already watched or build a per-creator engagement timeline, see the sister [studiomeyer-io/n8n-templates](https://github.com/studiomeyer-io/n8n-templates) repo.

## Related templates

- [08 - RSS to Multi-Channel Social](../08-rss-to-multi-channel-social/) · same RSS-parse pattern with multi-channel social fan-out
- [11 - Email to Notion](../11-email-to-notion/) · same Notion-write pattern with IMAP trigger
- [09 - Calendar Conflict Detector](../09-calendar-conflict-detector/) · same Schedule trigger + multi-source pattern
- [05 - Slack Channel Daily Digest](../05-slack-channel-daily-digest/) · same multi-provider LLM Switch pattern

---

*Built by [StudioMeyer](https://studiomeyer.io) in Mallorca. Issues + ideas at [github.com/studiomeyer-io/n8n-workflows/issues](https://github.com/studiomeyer-io/n8n-workflows/issues).*
