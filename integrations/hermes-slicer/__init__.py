from __future__ import annotations

import importlib.util
import os
from pathlib import Path


def _load_tool_module():
    root = Path(os.environ.get("HERMES_SLICER_ROOT", Path(__file__).resolve().parents[2])).resolve()
    module_path = root / "integrations" / "hermes_agent_tool.py"
    spec = importlib.util.spec_from_file_location("hermes_slicer_hermes_agent_tool", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load HermesSlicer tool module from {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def register(ctx):
    return _load_tool_module().register(ctx)
