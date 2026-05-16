from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any


SECRET_ENV_NAMES = (
    "AZURE_SPEECH_KEY",
    "AZURE_SPEECH_REGION",
    "MINIMAX_API_KEY",
    "DEEPSEEK_API_KEY",
    "SILICONFLOW_API_KEY",
    "HERMES_MCP_ENDPOINT",
    "HERMES_MCP_TOKEN",
)

_HOME = str(Path.home())
_PRIVATE_ROOT = Path(os.environ.get("HERMES_PRIVATE_ROOT", "G:/Private"))

_REDACTION_PATTERNS = (
    (re.compile(r"(?i)(authorization)\s*[:=]\s*bearer\s+[A-Za-z0-9._\-]+"), r"\1: <REDACTED>"),
    (re.compile(r"(?i)(api[_-]?key|secret|token)\s*[:=]\s*[A-Za-z0-9._\-]{8,}"), r"\1=<REDACTED>"),
    (re.compile(r"(?i)[A-Z]:[\\/]+Private(?:[\\/]+[^\s\"'<>]+)?"), "<PRIVATE_PATH>"),
)


def private_root() -> Path:
    return _PRIVATE_ROOT


def sanitize_text(value: Any, limit: int | None = 4000) -> str:
    text = str(value)
    if _HOME:
        text = text.replace(_HOME, "<USER_HOME>")
    for pattern, replacement in _REDACTION_PATTERNS:
        text = pattern.sub(replacement, text)
    if limit is not None and len(text) > limit:
        return text[:limit] + "...<truncated>"
    return text


def sanitize_obj(value: Any) -> Any:
    if isinstance(value, dict):
        return {sanitize_text(k, None): sanitize_obj(v) for k, v in value.items()}
    if isinstance(value, list):
        return [sanitize_obj(v) for v in value]
    if isinstance(value, tuple):
        return [sanitize_obj(v) for v in value]
    if isinstance(value, (str, Path)):
        return sanitize_text(value)
    return value


def is_private_path(path: Path) -> bool:
    try:
        candidate = path.resolve()
    except OSError:
        candidate = path.absolute()
    try:
        private = _PRIVATE_ROOT.resolve()
    except OSError:
        private = _PRIVATE_ROOT.absolute()
    try:
        candidate.relative_to(private)
        return True
    except ValueError:
        return False


def secret_presence() -> dict[str, Any]:
    env = {name: bool(os.environ.get(name)) for name in SECRET_ENV_NAMES}
    secrets_file = private_root() / "HermesOrca" / "secrets.env"
    file_keys: dict[str, bool] = {}
    if secrets_file.exists():
        for raw_line in secrets_file.read_text(errors="ignore").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            if key in SECRET_ENV_NAMES:
                file_keys[key] = bool(value.strip())
    return {
        "env": env,
        "private_root_present": private_root().exists(),
        "project_secret_file_present": secrets_file.exists(),
        "file_keys_present": file_keys,
    }
