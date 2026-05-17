from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from hermes_slicer.bridge import TTS_ENABLE_ENV, tts_speak  # noqa: E402
from hermes_slicer.proof import log_event, write_json  # noqa: E402
from hermes_slicer.security import secret_presence  # noqa: E402
from hermes_slicer.voices import load_voice_catalog  # noqa: E402


PROBE_REQUEST = {
    "text": "HermesSlicer TTS probe.",
    "voice": "en-US-JennyNeural",
    "agent": "orchestrator",
}


def build_report() -> dict[str, Any]:
    result = tts_speak(PROBE_REQUEST)
    catalog = load_voice_catalog()
    secrets = secret_presence()
    env = secrets.get("env", {})
    status = str(result.get("status", "failed"))
    return {
        "status": status,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "action": "tts.speak",
        "agent": result.get("agent", PROBE_REQUEST["agent"]),
        "voice": result.get("voice", PROBE_REQUEST["voice"]),
        "playback": result.get("playback", "not_attempted"),
        "reason": result.get("reason") or result.get("error") or "",
        "request": PROBE_REQUEST,
        "result": result,
        "catalog_source": catalog.get("source"),
        "catalog_voice_count": catalog.get("count"),
        "azure_key_present": bool(env.get("AZURE_SPEECH_KEY")),
        "azure_region_present": bool(env.get("AZURE_SPEECH_REGION")),
        "tts_opt_in_present": os.environ.get(TTS_ENABLE_ENV) == "1",
        "azure_gate": {
            "azure_key_present": bool(env.get("AZURE_SPEECH_KEY")),
            "azure_region_present": bool(env.get("AZURE_SPEECH_REGION")),
            "tts_opt_in_env": TTS_ENABLE_ENV,
            "tts_opt_in_present": os.environ.get(TTS_ENABLE_ENV) == "1",
            "live_playback_adapter": "not_implemented_in_v1",
        },
    }


def main() -> int:
    report = build_report()
    write_json(ROOT / "proof" / "runtime" / "hermes-tool-tts_speak.json", report)
    log_event(
        "proof",
        "hermes_tool.tts_speak",
        report["status"],
        inputs={"action": "tts.speak", "agent": report["agent"], "voice": report["voice"]},
        outputs={
            "status": report["status"],
            "playback": report["playback"],
            "azure_key_present": report["azure_key_present"],
            "azure_region_present": report["azure_region_present"],
            "tts_opt_in_present": report["tts_opt_in_present"],
        },
        proof_files=["proof/runtime/hermes-tool-tts_speak.json"],
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] in {"passed", "blocked"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
