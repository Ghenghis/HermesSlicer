# Azure Voices Report

Date: 2026-05-16

## Sources

- https://learn.microsoft.com/en-us/azure/ai-services/speech-service/rest-text-to-speech
- `G:\Github\Hermes_OrcaSlicer_Codex_Contract_Kit\security\PRIVATE_DATA_RULES.md`

## Observed

- Azure Speech exposes a REST endpoint for listing available voices for a region.
- The endpoint requires a Speech resource credential.
- Microsoft documents `ShortName`, `Locale`, `Gender`, `VoiceType`, and other voice metadata in the response.

## Local Credential Probe

Command run:

```powershell
$names=@('AZURE_SPEECH_KEY','AZURE_SPEECH_REGION','MINIMAX_API_KEY','DEEPSEEK_API_KEY','SILICONFLOW_API_KEY','HERMES_MCP_ENDPOINT','HERMES_MCP_TOKEN'); foreach($n in $names){ [bool][Environment]::GetEnvironmentVariable($n) }
```

Observed: all required provider environment variables were absent in this shell. Private root exists, but no project secret file was read or copied.

## TTS Smoke Test

Command run:

```powershell
python scripts\smoke_bridge.py
```

Observed output excerpt:

```text
tts_blocked: HTTP 200
"status": "blocked"
"playback": "not_attempted"
"reason": "Azure Speech credentials are not present in this shell."
```

## Implementation

- `config/voices.azure.en.json` is a generated safe English neural voice catalog.
- `/api/voices/azure/en` returns only catalog entries, never credentials.
- `/api/tts/speak` validates voice/text requests and blocks playback safely until Azure credentials and a live playback adapter are enabled.
- Live Azure SDK/REST listing and playback are intentionally not enabled in V1.

## Decision

Use the generated English voice catalog for V1. Add live Azure voice refresh later only after credentials are present through environment or the approved local secret adapter.

## Risks

- Catalog may lag Azure's live voice list.
- Full TTS playback remains blocked without credentials; this is a deliberate safety result for V1 proof.
