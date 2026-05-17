# Claude Audit Output Folder

Claude and Claude-spawned agents may write Markdown audit outputs here only.

Codex review note: these files are preserved audit evidence, not release policy. Where a Claude audit file conflicts with `CODEX_REVIEW_NOTES.md`, `V1_RELEASE_CHECKLIST.md`, or `proof/runtime/v1-release-checklist.json`, the Codex-reviewed generated checklist is authoritative.

Required final packet:

- `00_EXECUTIVE_SUMMARY.md`
- `01_E2E_COMPLETION_AUDIT.md`
- `02_GAP_REGISTER.md`
- `03_BLOCKERS_AND_EXTERNAL_GATES.md`
- `04_CODEX_FIX_QUEUE.md`
- `05_EVIDENCE_INDEX.md`

Optional raw agent reports:

- `agents/<agent-name>.md`

Do not place source code, JSON proof artifacts, screenshots, logs, or generated binaries in this folder.
