from __future__ import annotations

import importlib.util
import os
from pathlib import Path


def _candidate_roots():
    env_root = os.environ.get("HERMES_SLICER_ROOT", "").strip()
    if env_root:
        yield Path(env_root)
    cwd = Path.cwd()
    yield cwd
    yield from cwd.parents
    yield from Path(__file__).resolve().parents


def _resolve_root() -> Path:
    seen: set[Path] = set()
    for candidate in _candidate_roots():
        try:
            root = candidate.expanduser().resolve()
        except (OSError, RuntimeError):
            continue
        if root in seen:
            continue
        seen.add(root)
        if (root / "integrations" / "hermes_agent_tool.py").exists():
            return root
    raise RuntimeError(
        "Could not locate HermesSlicer root. Set HERMES_SLICER_ROOT or run hermes from the HermesSlicer repo."
    )


def _load_tool_module():
    root = _resolve_root()
    module_path = root / "integrations" / "hermes_agent_tool.py"
    spec = importlib.util.spec_from_file_location("hermes_slicer_hermes_agent_tool", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load HermesSlicer tool module from {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def register(ctx):
    return _load_tool_module().register(ctx)
