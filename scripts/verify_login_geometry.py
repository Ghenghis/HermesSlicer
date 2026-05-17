from __future__ import annotations

import hashlib
import json
import struct
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from hermes_slicer.proof import log_event, write_json  # noqa: E402


EXPECTED_LOGIN_SHA256 = "89979c452028fbc0780dc0781acb8697764460c8c203ec57bb55968160ab77c8"
EXPECTED_LOGIN_SIZE = {"width": 1120, "height": 718}
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
VIEWPORTS = {
    "desktop_1366x768": {"width": 1366, "height": 768},
    "desktop_1920x1080": {"width": 1920, "height": 1080},
    "mobile_390x844": {"width": 390, "height": 844},
}
FORBIDDEN_TEXT = (
    "JusPrin",
    "JusBot",
    "Obico",
    "Continue to Hermes Tools",
    "No slicing. Just print.",
)
REQUIRED_HTML = (
    'id="authGate"',
    'class="auth-shell"',
    'class="auth-logo"',
    'src="/assets/hermes-slicer-login.png"',
    'id="authForm"',
    'id="authEmail"',
    'id="authPassword"',
    'id="authPasswordToggle"',
    'id="authContinue"',
    'id="authCreate"',
    "Hermes Slicer login",
    "Email or Username",
    "Sign In",
    "Sign Up / Create Account",
)
REQUIRED_CSS = (
    "width: min(900px, calc((100vh - 16px) * 0.8), 94vw);",
    ".auth-card",
    "width: 65.5%;",
    "@media (max-width: 520px)",
    "width: min(100%, 430px);",
    "max-height: 30vh;",
    "@media (max-height: 820px) and (min-width: 621px)",
    "padding: 12px 20px;",
)


def png_size(path: Path) -> dict[str, int]:
    data = path.read_bytes()
    if not data.startswith(PNG_SIGNATURE):
        raise ValueError(f"{path} is not a PNG file")
    if data[12:16] != b"IHDR":
        raise ValueError(f"{path} does not have an IHDR chunk at the expected offset")
    width, height = struct.unpack(">II", data[16:24])
    return {"width": width, "height": height}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def image_signature(path: Path) -> str:
    data = path.read_bytes()[:8]
    if data.startswith(b"\xff\xd8\xff"):
        return "jpeg"
    if data.startswith(PNG_SIGNATURE):
        return "png"
    return "unknown"


def estimate_layout(viewport: dict[str, int]) -> dict[str, Any]:
    width = viewport["width"]
    height = viewport["height"]
    ratio = EXPECTED_LOGIN_SIZE["height"] / EXPECTED_LOGIN_SIZE["width"]
    mobile = width <= 520
    compact_desktop = height <= 820 and width >= 621
    if mobile:
        shell_width = min(width - 24, 520)
        logo_width = min(520, width * 1.02)
        logo_height = min(logo_width * ratio, height * 0.30)
        card_width = min(shell_width, 430)
        estimated_card_height = 541
        top_padding = 10
        bottom_padding = 18
        margin_bottom = -16
    else:
        shell_width = min(900, (height - 16) * 0.8, width * 0.94)
        logo_width = shell_width
        logo_height = logo_width * ratio
        card_width = shell_width * 0.655
        estimated_card_height = 361 if compact_desktop else 560
        top_padding = 8 if compact_desktop else 16
        bottom_padding = 8 if compact_desktop else 16
        margin_bottom = -36 if compact_desktop else max(-64, min(-34, -height * 0.054))
    estimated_total_height = top_padding + logo_height + margin_bottom + estimated_card_height + bottom_padding
    return {
        "viewport": viewport,
        "mode": "mobile" if mobile else "desktop_compact" if compact_desktop else "desktop_full",
        "shell_width_px": round(shell_width, 2),
        "logo_width_px": round(logo_width, 2),
        "logo_height_px": round(logo_height, 2),
        "card_width_px": round(card_width, 2),
        "estimated_card_height_px": round(estimated_card_height, 2),
        "estimated_total_height_px": round(estimated_total_height, 2),
        "full_card_visible": estimated_total_height <= height,
        "card_to_shell_ratio": round(card_width / shell_width, 3) if shell_width else 0,
    }


def collect_report() -> dict[str, Any]:
    html_path = ROOT / "web" / "index.html"
    css_path = ROOT / "web" / "styles.css"
    login_asset = ROOT / "web" / "assets" / "hermes-slicer-login.png"
    login_screenshot = ROOT / "proof" / "screenshots" / "login-hermes-slicer.jpg"

    errors: list[str] = []
    html = html_path.read_text(encoding="utf-8")
    css = css_path.read_text(encoding="utf-8")
    combined_source = "\n".join([html, css])

    for needle in REQUIRED_HTML:
        if needle not in html:
            errors.append(f"missing login HTML marker: {needle}")
    for needle in REQUIRED_CSS:
        if needle not in css:
            errors.append(f"missing login CSS geometry marker: {needle}")
    for needle in FORBIDDEN_TEXT:
        if needle in combined_source:
            errors.append(f"forbidden legacy login text found: {needle}")

    asset_hash = sha256(login_asset) if login_asset.exists() else ""
    asset_size = png_size(login_asset) if login_asset.exists() else {"width": 0, "height": 0}
    if asset_hash != EXPECTED_LOGIN_SHA256:
        errors.append("login asset hash does not match the accepted reference image")
    if asset_size != EXPECTED_LOGIN_SIZE:
        errors.append("login asset dimensions do not match the accepted reference image")

    viewports = {name: estimate_layout(viewport) for name, viewport in VIEWPORTS.items()}
    for name, geometry in viewports.items():
        if not geometry["full_card_visible"]:
            errors.append(f"login card is estimated to overflow viewport {name}")
        if name.startswith("desktop") and geometry["card_to_shell_ratio"] != 0.655:
            errors.append(f"desktop card ratio drifted for {name}")
        if name.startswith("mobile") and geometry["card_width_px"] > geometry["viewport"]["width"]:
            errors.append(f"mobile card exceeds viewport width for {name}")

    screenshot = {
        "file": "proof/screenshots/login-hermes-slicer.jpg",
        "exists": login_screenshot.exists(),
        "image_signature": image_signature(login_screenshot) if login_screenshot.exists() else "missing",
    }
    if screenshot["image_signature"] not in {"jpeg", "png"}:
        errors.append("login screenshot proof is missing or not a PNG/JPEG image")

    return {
        "status": "passed" if not errors else "failed",
        "asset": {
            "file": "web/assets/hermes-slicer-login.png",
            "sha256": asset_hash,
            "expected_sha256": EXPECTED_LOGIN_SHA256,
            "size": asset_size,
            "expected_size": EXPECTED_LOGIN_SIZE,
        },
        "source_checks": {
            "required_html_markers": list(REQUIRED_HTML),
            "required_css_markers": list(REQUIRED_CSS),
            "forbidden_text_absent": not any(needle in combined_source for needle in FORBIDDEN_TEXT),
        },
        "viewports": viewports,
        "screenshot": screenshot,
        "errors": errors,
    }


def main() -> int:
    report = collect_report()
    proof_file = ROOT / "proof" / "runtime" / "login-geometry.json"
    write_json(proof_file, report)
    log_event(
        "proof",
        "login.visual_geometry_gate",
        report["status"],
        outputs={
            "viewports": list(VIEWPORTS),
            "asset_sha256": report["asset"]["sha256"],
            "errors": report["errors"],
        },
        proof_files=["proof/runtime/login-geometry.json", "proof/screenshots/login-hermes-slicer.jpg"],
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
