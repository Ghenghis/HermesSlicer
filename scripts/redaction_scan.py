from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
TEXT_SUFFIXES = {".md", ".json", ".jsonl", ".yaml", ".yml", ".txt", ".html", ".js", ".ts", ".py", ".css", ".ps1", ".toml"}
PATTERNS = [
    re.compile(r"(?i)(api[_-]?key|secret|token|authorization|bearer)\s*[:=]\s*[A-Za-z0-9_\-.]{12,}"),
    re.compile(r"(?i)G:\\Private\\[^\s]+"),
    re.compile(r"-----BEGIN (RSA |OPENSSH |EC |)PRIVATE KEY-----"),
]
SKIP_DIRS = {".git", "__pycache__", "node_modules", "dist", "build", ".pytest_cache", "upstream"}


def main() -> int:
    violations: list[str] = []
    for path in ROOT.rglob("*"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        text = path.read_text(errors="ignore")
        for pattern in PATTERNS:
            if pattern.search(text):
                violations.append(str(path))
                break
    if violations:
        print("REDACTION SCAN FAILED")
        print("\n".join(violations))
        return 1
    print("REDACTION SCAN PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
