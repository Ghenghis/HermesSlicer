from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .config import CONFIG_DIR


DEFAULT_ENGLISH_VOICES = [
    {"short_name": "en-US-JennyNeural", "display_name": "Jenny", "locale": "en-US", "gender": "Female"},
    {"short_name": "en-US-GuyNeural", "display_name": "Guy", "locale": "en-US", "gender": "Male"},
    {"short_name": "en-US-AriaNeural", "display_name": "Aria", "locale": "en-US", "gender": "Female"},
    {"short_name": "en-US-DavisNeural", "display_name": "Davis", "locale": "en-US", "gender": "Male"},
    {"short_name": "en-GB-MaisieNeural", "display_name": "Maisie", "locale": "en-GB", "gender": "Female"},
    {"short_name": "en-GB-RyanNeural", "display_name": "Ryan", "locale": "en-GB", "gender": "Male"},
    {"short_name": "en-AU-CarlyNeural", "display_name": "Carly", "locale": "en-AU", "gender": "Female"},
    {"short_name": "en-AU-WilliamNeural", "display_name": "William", "locale": "en-AU", "gender": "Male"},
    {"short_name": "en-CA-ClaraNeural", "display_name": "Clara", "locale": "en-CA", "gender": "Female"},
    {"short_name": "en-CA-LiamNeural", "display_name": "Liam", "locale": "en-CA", "gender": "Male"},
    {"short_name": "en-IN-NeerjaNeural", "display_name": "Neerja", "locale": "en-IN", "gender": "Female"},
    {"short_name": "en-NZ-MollyNeural", "display_name": "Molly", "locale": "en-NZ", "gender": "Female"},
]


def catalog_path() -> Path:
    return CONFIG_DIR / "voices.azure.en.json"


def load_voice_catalog() -> dict[str, Any]:
    path = catalog_path()
    if path.exists():
        voices = json.loads(path.read_text(encoding="utf-8")).get("voices", DEFAULT_ENGLISH_VOICES)
    else:
        voices = DEFAULT_ENGLISH_VOICES
    english = [voice for voice in voices if str(voice.get("locale", "")).startswith("en-")]
    return {
        "source": "generated_safe_catalog",
        "live_azure_call": False,
        "count": len(english),
        "voices": english,
    }
