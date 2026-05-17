# Codex Review Notes on Claude Audit

Date: 2026-05-17

Claude's Markdown audit packet is preserved in this folder as audit evidence, but Codex does not accept every recommendation as release policy.

## Accepted

- V1 is not tag-ready while the generated checklist reports unresolved live Hermes Agent, AS_USER, Hermes Proof MCP, and computer-use gates.
- The audit packet belongs in the main proof tree, not only in `.claude/worktrees/...`.
- `pyproject.toml` should expose the existing AGPL-3.0-only license posture.
- AS_USER should have a standalone proof artifact.
- Proof validation should directly inspect key tool/FLSUN runtime artifacts.
- Proof scripts should fail fast if the active Hermes CLI is not `v0.14.0 (2026.5.16)`.

## Rejected Or Deferred

- Codex must not invent owner names, dates, rationale, or acceptance decisions. Owner acceptance is a project-owner decision, not an engineering fact.
- Owner acceptance alone does not make missing live Hermes Agent, Proof MCP, AS_USER, or computer-use proof true. Any V1 tag using owner acceptance must be explicitly scoped as a local sidecar release with those capabilities excluded or deferred.
- A live MCP writer script is not enough to prove MCP by itself. A real workspace-scoped transport, MCP registration, and evidence verification path are still required.

## Codex Next Slice

Codex is implementing only safe local improvements in this pass: rescue the audit packet into `proof/claude_audits/`, ignore `.claude/`, add license metadata, add AS_USER proof output, strengthen proof validation, add Hermes v0.14 script guards, and add focused tests.
