Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

python -m hermes_slicer.bridge --host 127.0.0.1 --port 8765
