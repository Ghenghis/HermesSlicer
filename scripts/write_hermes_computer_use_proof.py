from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from hermes_slicer.config import as_user_session_gate  # noqa: E402
from hermes_slicer.proof import log_event, write_json  # noqa: E402

VISUAL_PROOF_PATH_ENV = "HERMES_COMPUTER_USE_VISUAL_PROOF_PATH"


def run_command(args: list[str]) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            args,
            cwd=str(ROOT),
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"status": "blocked", "args": args, "error_type": type(exc).__name__, "reason": str(exc)}
    return {
        "status": "passed" if completed.returncode == 0 else "failed",
        "args": args,
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }


def visual_proof_gate() -> dict[str, Any]:
    value = os.environ.get(VISUAL_PROOF_PATH_ENV, "").strip()
    configured = bool(value)
    if not configured:
        return {
            "configured": False,
            "passed": False,
            "reason": f"{VISUAL_PROOF_PATH_ENV} is not set.",
            "required": [VISUAL_PROOF_PATH_ENV, "existing proof file under proof/"],
        }
    path = Path(value)
    if not path.is_absolute():
        path = ROOT / path
    try:
        resolved = path.resolve()
        proof_root = (ROOT / "proof").resolve()
    except (OSError, RuntimeError) as exc:
        return {"configured": True, "passed": False, "path": value, "reason": f"Could not resolve visual proof path: {exc}"}
    if proof_root not in [resolved, *resolved.parents]:
        return {
            "configured": True,
            "passed": False,
            "path": str(resolved),
            "reason": "Visual proof must be stored under the HermesSlicer proof/ directory.",
        }
    if not resolved.exists() or not resolved.is_file():
        return {"configured": True, "passed": False, "path": str(resolved), "reason": "Visual proof file does not exist."}
    return {"configured": True, "passed": True, "path": str(resolved), "reason": "Visual proof file exists under proof/."}


def build_report() -> dict[str, Any]:
    hermes_path = shutil.which("hermes") or shutil.which("hermes.exe")
    status_result = run_command([hermes_path, "computer-use", "status"]) if hermes_path else {"status": "blocked", "reason": "hermes CLI not found"}
    cua_path = shutil.which("cua-driver")
    supported_platform = sys.platform == "darwin"
    installed = bool(cua_path)
    as_user = as_user_session_gate()
    visual_proof = visual_proof_gate()
    available = supported_platform and installed and as_user.get("granted") is True and visual_proof.get("passed") is True
    if available:
        reason = "Hermes Agent computer-use backend is installed with bounded AS_USER and visual proof."
    elif not supported_platform:
        reason = f"Hermes Agent v0.14 computer-use backend is macOS-only; current platform is {platform.system()}."
    else:
        missing = []
        if not installed:
            missing.append("cua-driver is not installed")
        if as_user.get("granted") is not True:
            missing.append("bounded AS_USER grant is not active")
        if visual_proof.get("passed") is not True:
            missing.append("visual proof run is missing")
        reason = "; ".join(missing) + "."
    return {
        "status": "passed" if available else "blocked",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "computer_use": {
            "available": available,
            "supported_platform": supported_platform,
            "platform": platform.system(),
            "cua_driver_installed": installed,
            "cua_driver_path_present": bool(cua_path),
            "hermes_status_command": status_result,
            "as_user_session": as_user,
            "visual_proof": visual_proof,
            "reason": reason,
            "required": ["macOS host", "cua-driver installed", "bounded AS_USER grant", "visual proof run"],
        },
    }


def main() -> int:
    report = build_report()
    write_json(ROOT / "proof" / "runtime" / "hermes-computer-use.json", report)
    log_event(
        "proof",
        "hermes.computer_use_status",
        report["status"],
        outputs={"status": report["status"], "available": report["computer_use"]["available"]},
        proof_files=["proof/runtime/hermes-computer-use.json"],
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
