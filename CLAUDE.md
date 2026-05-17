# Claude Operating Note

For HermesSlicer V1 audit work, read and follow `CLAUDE_AUDIT_CONTRACT.md` before doing anything else.

Default mode for Claude and Claude-spawned agents in this repo is audit-only:

- Create or update Markdown audit files only under `proof/claude_audits/`.
- Do not edit source code, tests, runtime proof JSON, screenshots, assets, submodules, lock files, or configuration.
- Do not claim Hermes Agent is working unless the repo proof shows Hermes Agent `v0.14.0 (2026.5.16)` and the relevant gate passes.
- Do not claim Hermes Proof MCP, AS_USER, live-agent, or computer-use is complete unless the matching proof gate passes.
- Hand findings back to Codex as Markdown with file paths, evidence, priority, and next actions.

