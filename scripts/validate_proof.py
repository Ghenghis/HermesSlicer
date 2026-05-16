from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from hermes_slicer.proof import LEDGER_PATH, validate_ledger, write_json  # noqa: E402


def main() -> int:
    report = validate_ledger(LEDGER_PATH)
    write_json(ROOT / "proof" / "runtime" / "proof-validation.json", report)
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
