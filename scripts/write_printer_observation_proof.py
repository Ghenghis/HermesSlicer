from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from hermes_slicer.printers import observe_printers  # noqa: E402
from hermes_slicer.proof import log_event, write_json  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write read-only local printer observation proof.")
    parser.add_argument("--target-id", default="", help="Optional printer target id from config/printers.example.json or local/printers.json.")
    args = parser.parse_args(argv)

    body = {"target_id": args.target_id} if args.target_id else {}
    report = observe_printers(body)
    output = ROOT / "proof" / "runtime" / "printer-observation.json"
    write_json(output, report)
    log_event(
        "proof",
        "printer.observation",
        report["status"],
        inputs=body,
        outputs={
            "status": report["status"],
            "targets": [item["target"]["id"] for item in report.get("targets", []) if isinstance(item, dict)],
            "safety_mode": report.get("safety", {}).get("mode"),
        },
        proof_files=["proof/runtime/printer-observation.json"],
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
