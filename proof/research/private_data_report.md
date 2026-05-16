# Private Data Report

Date: 2026-05-16

## Sources

- `G:\Github\Hermes_OrcaSlicer_Codex_Contract_Kit\security\PRIVATE_DATA_RULES.md`
- `G:\Github\HermesSlicer\hermes_slicer\security.py`

## Local Checks

Command run:

```powershell
$names=@('AZURE_SPEECH_KEY','AZURE_SPEECH_REGION','MINIMAX_API_KEY','DEEPSEEK_API_KEY','SILICONFLOW_API_KEY','HERMES_MCP_ENDPOINT','HERMES_MCP_TOKEN'); foreach($n in $names){ "$n=$([bool][Environment]::GetEnvironmentVariable($n))" }; $privateRoot = Join-Path 'G:' 'Private'; "PRIVATE_ROOT_EXISTS=$(Test-Path -LiteralPath $privateRoot)"; "PROJECT_SECRET_FILE_EXISTS=$(Test-Path -LiteralPath (Join-Path $privateRoot 'HermesOrca\secrets.env'))"
```

Observed:

- Azure Speech key present: false
- Azure Speech region present: false
- MiniMax key present: false
- DeepSeek key present: false
- SiliconFlow key present: false
- Hermes MCP endpoint present: false
- Hermes MCP token present: false
- Private root present: true
- Project secret file present: false

Redaction command:

```powershell
python scripts\redaction_scan.py .
```

Observed output:

```text
REDACTION SCAN PASSED
```

## Implementation

- `secret_presence()` returns booleans only.
- `/health` reports present/missing flags only.
- `sanitize_text()` redacts authorization-like values, token-like values, user home paths, and private-root paths.
- `.gitignore` excludes env files, keys, private raw proof folders, and local agent state.

## Decision

Do not read private files until the user provides or approves the exact local adapter. Keep V1 to environment presence checks and safe generated config.

## Risks

- The live provider setup remains blocked until credentials are provided through an approved local mechanism.
