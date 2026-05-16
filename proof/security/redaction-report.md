# Redaction Report

Date: 2026-05-16

Command:

```powershell
python scripts\redaction_scan.py .
```

Observed:

```text
REDACTION SCAN PASSED
```

Scope note: `scripts/redaction_scan.py` skips pinned upstream submodules under `upstream/`. Those repositories are tracked by commit in `.gitmodules`/gitlinks and are not local proof or secret-output artifacts.

Decision: proof and source tree passed the local redaction scan after runtime proof generation.
