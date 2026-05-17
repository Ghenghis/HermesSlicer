from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from hermes_slicer.config import as_user_session_gate  # noqa: E402
from hermes_slicer.proof import log_event, write_json  # noqa: E402


def build_report() -> dict[str, object]:
    gate = as_user_session_gate()
    return {
        "status": gate["status"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "as_user_session": gate,
    }


def main() -> int:
    report = build_report()
    write_json(ROOT / "proof" / "runtime" / "as_user_session.json", report)
    log_event(
        "proof",
        "as_user.session_status",
        str(report["status"]),
        outputs={
            "status": report["status"],
            "granted": report["as_user_session"].get("granted") if isinstance(report["as_user_session"], dict) else False,
        },
        proof_files=["proof/runtime/as_user_session.json"],
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
