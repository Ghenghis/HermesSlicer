from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from hermes_slicer.proof import write_json


SCREENSHOTS = ["panel-open.png", "panel-flsun.png", "panel-hidden.png"]
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def main() -> int:
    results = []
    ok = True
    for name in SCREENSHOTS:
        path = ROOT / "proof" / "screenshots" / name
        signature = path.read_bytes()[:8] if path.exists() else b""
        is_png = signature == PNG_SIGNATURE
        ok = ok and is_png
        results.append({"file": f"proof/screenshots/{name}", "exists": path.exists(), "png_signature": is_png})
    report = {"status": "passed" if ok else "failed", "screenshots": results}
    write_json(ROOT / "proof" / "runtime" / "screenshot-format.json", report)
    print(json.dumps(report, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
