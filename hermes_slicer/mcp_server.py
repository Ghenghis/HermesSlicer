from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, TextIO

from . import __version__
from .bridge import ACTION_ROUTES, dispatch_action, secret_presence_summary
from .config import ALLOWED_ACTIONS, ROOT
from .proof import validate_ledger
from .security import sanitize_obj


JSONRPC_VERSION = "2.0"
PROTOCOL_VERSION = "2024-11-05"
SERVER_NAME = "hermes-slicer-proof"
EXPECTED_WORKSPACE_ROOT = ROOT

ERROR_PARSE = -32700
ERROR_INVALID_REQUEST = -32600
ERROR_METHOD_NOT_FOUND = -32601
ERROR_INVALID_PARAMS = -32602
ERROR_INTERNAL = -32603


class JsonRpcError(Exception):
    def __init__(self, code: int, message: str, data: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.data = data


def workspace_scope_gate(workspace_root: str | Path | None = None) -> dict[str, Any]:
    candidate = Path(workspace_root) if workspace_root else EXPECTED_WORKSPACE_ROOT
    expected = EXPECTED_WORKSPACE_ROOT
    try:
        candidate_resolved = candidate.resolve()
    except OSError:
        candidate_resolved = candidate.absolute()
    try:
        expected_resolved = expected.resolve()
    except OSError:
        expected_resolved = expected.absolute()
    workspace_scope_ok = _same_path(candidate_resolved, expected_resolved)
    return {
        "status": "passed" if workspace_scope_ok else "blocked",
        "workspace_scope_ok": workspace_scope_ok,
        "workspace_root": str(candidate_resolved),
        "expected_workspace_root": str(expected_resolved),
        "reason": "Workspace root matches HermesSlicer." if workspace_scope_ok else "MCP server is not scoped to this HermesSlicer workspace.",
    }


def tool_definitions() -> list[dict[str, Any]]:
    tools = []
    action_by_id = {str(action["id"]): action for action in ALLOWED_ACTIONS}
    for action_id in sorted(ACTION_ROUTES):
        action = action_by_id.get(action_id, {})
        tools.append(
            {
                "name": action_id,
                "description": action.get("description", f"Run safe HermesSlicer action {action_id}."),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "workspace_root": {
                            "type": "string",
                            "description": "Must resolve to this HermesSlicer checkout.",
                        },
                        "payload": {
                            "type": "object",
                            "description": "Optional bridge action payload.",
                        },
                    },
                    "additionalProperties": True,
                },
                "annotations": {
                    "title": action_id,
                    "readOnlyHint": True,
                    "destructiveHint": bool(action.get("destructive", False)),
                },
            }
        )
    tools.append(
        {
            "name": "hermes.verify_evidence",
            "description": "Verify sanitized HermesSlicer proof ledger evidence for this workspace.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "workspace_root": {
                        "type": "string",
                        "description": "Must resolve to this HermesSlicer checkout.",
                    }
                },
                "required": ["workspace_root"],
                "additionalProperties": False,
            },
            "annotations": {
                "title": "hermes.verify_evidence",
                "readOnlyHint": True,
                "destructiveHint": False,
            },
        }
    )
    return tools


def handle_request(request: dict[str, Any]) -> dict[str, Any] | None:
    if request.get("jsonrpc") != JSONRPC_VERSION:
        raise JsonRpcError(ERROR_INVALID_REQUEST, "jsonrpc must be '2.0'")
    method = request.get("method")
    request_id = request.get("id")
    if not isinstance(method, str):
        raise JsonRpcError(ERROR_INVALID_REQUEST, "method is required")

    if method in {"notifications/initialized", "$/cancelRequest"}:
        return None
    if method == "initialize":
        return _response(request_id, _initialize_result())
    if method == "ping":
        return _response(request_id, {})
    if method == "tools/list":
        return _response(request_id, {"tools": tool_definitions()})
    if method == "tools/call":
        return _response(request_id, call_tool(_params_dict(request.get("params"))))
    raise JsonRpcError(ERROR_METHOD_NOT_FOUND, f"Unknown method: {method}")


def call_tool(params: dict[str, Any]) -> dict[str, Any]:
    name = params.get("name")
    arguments = params.get("arguments", {})
    if not isinstance(name, str) or not name:
        raise JsonRpcError(ERROR_INVALID_PARAMS, "tools/call requires a tool name")
    if arguments is None:
        arguments = {}
    if not isinstance(arguments, dict):
        raise JsonRpcError(ERROR_INVALID_PARAMS, "tools/call arguments must be an object")

    gate = workspace_scope_gate(arguments.get("workspace_root"))
    if not gate["workspace_scope_ok"]:
        return _tool_result(gate, is_error=True)

    if name == "hermes.verify_evidence":
        ledger = validate_ledger()
        artifact_report = _validate_runtime_artifacts()
        evidence_ok = ledger["status"] == "passed" and artifact_report["status"] == "passed"
        payload = {
            "status": "passed" if evidence_ok else "blocked",
            "proof_mcp": {
                "available": evidence_ok,
                "workspace_root": gate["workspace_root"],
                "expected_workspace_root": gate["expected_workspace_root"],
                "workspace_scope_ok": True,
                "evidence_ledger_ok": ledger["status"] == "passed",
                "artifact_report_ok": artifact_report["status"] == "passed",
            },
            "ledger": ledger,
            "artifact_report": artifact_report,
            "secrets": secret_presence_summary(),
        }
        return _tool_result(payload, is_error=payload["status"] != "passed")

    if name not in ACTION_ROUTES:
        raise JsonRpcError(ERROR_INVALID_PARAMS, f"Unknown tool: {name}")

    payload_arg = arguments.get("payload", {})
    bridge_payload = payload_arg if isinstance(payload_arg, dict) else {}
    if name == "hermes_agent.tool_request" and "message" in arguments:
        bridge_payload = {**bridge_payload, "message": arguments["message"]}
    result, status = dispatch_action({"action": name, "payload": bridge_payload})
    response_payload = {
        "status": "passed" if 200 <= status < 300 else "failed",
        "workspace_root": gate["workspace_root"],
        "workspace_scope_ok": True,
        "action": name,
        "result": result,
    }
    return _tool_result(response_payload, is_error=status >= 400)


def run_stdio(stdin: TextIO = sys.stdin, stdout: TextIO = sys.stdout) -> None:
    for line in stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
            if not isinstance(request, dict):
                raise JsonRpcError(ERROR_INVALID_REQUEST, "request must be an object")
            response = handle_request(request)
        except json.JSONDecodeError as exc:
            response = _error_response(None, ERROR_PARSE, "Parse error", {"message": exc.msg})
        except JsonRpcError as exc:
            response = _error_response(_safe_request_id(line), exc.code, exc.message, exc.data)
        except Exception as exc:  # pragma: no cover - keeps stdio transport alive.
            response = _error_response(_safe_request_id(line), ERROR_INTERNAL, "Internal error", {"type": type(exc).__name__})
        if response is not None:
            stdout.write(json.dumps(sanitize_obj(response), ensure_ascii=True, sort_keys=True) + "\n")
            stdout.flush()


def self_test() -> dict[str, Any]:
    gate = workspace_scope_gate()
    tools = tool_definitions()
    return {
        "status": "passed" if gate["workspace_scope_ok"] and len(tools) >= len(ACTION_ROUTES) else "blocked",
        "server": SERVER_NAME,
        "version": __version__,
        "tool_count": len(tools),
        "workspace": gate,
        "secrets": secret_presence_summary(),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="HermesSlicer JSON-RPC stdio MCP server")
    parser.add_argument("--test", action="store_true", help="Run an offline self-test without starting stdio transport.")
    args = parser.parse_args(argv)
    if args.test:
        result = self_test()
        print(json.dumps(sanitize_obj(result), indent=2, sort_keys=True))
        return 0 if result["status"] == "passed" else 1
    run_stdio()
    return 0


def _initialize_result() -> dict[str, Any]:
    gate = workspace_scope_gate()
    if not gate["workspace_scope_ok"]:
        raise JsonRpcError(ERROR_INVALID_PARAMS, "Workspace root is not HermesSlicer.", gate)
    return {
        "protocolVersion": PROTOCOL_VERSION,
        "capabilities": {"tools": {"listChanged": False}},
        "serverInfo": {"name": SERVER_NAME, "version": __version__},
        "instructions": "Workspace-scoped read-only HermesSlicer proof and bridge tools. Secret values are never returned.",
        "workspace": gate,
    }


def _params_dict(params: Any) -> dict[str, Any]:
    if params is None:
        return {}
    if not isinstance(params, dict):
        raise JsonRpcError(ERROR_INVALID_PARAMS, "params must be an object")
    return params


def _tool_result(payload: dict[str, Any], is_error: bool = False) -> dict[str, Any]:
    safe_payload = _mcp_safe_obj(payload)
    return {
        "content": [{"type": "text", "text": json.dumps(safe_payload, indent=2, sort_keys=True)}],
        "structuredContent": safe_payload,
        "isError": is_error,
    }


def _response(request_id: Any, result: dict[str, Any]) -> dict[str, Any]:
    return {"jsonrpc": JSONRPC_VERSION, "id": request_id, "result": _mcp_safe_obj(result)}


def _error_response(request_id: Any, code: int, message: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
    error: dict[str, Any] = {"code": code, "message": message}
    if data is not None:
        error["data"] = _mcp_safe_obj(data)
    return {"jsonrpc": JSONRPC_VERSION, "id": request_id, "error": error}


def _safe_request_id(raw_line: str) -> Any:
    try:
        payload = json.loads(raw_line)
    except json.JSONDecodeError:
        return None
    if isinstance(payload, dict):
        return payload.get("id")
    return None


def _same_path(left: Path, right: Path) -> bool:
    return str(left).casefold() == str(right).casefold()


def _validate_runtime_artifacts() -> dict[str, Any]:
    try:
        from scripts.validate_proof import validate_artifacts
    except Exception as exc:  # pragma: no cover - import failures are reported as blocked evidence.
        return {
            "status": "blocked",
            "artifacts": {},
            "errors": [f"Could not import proof artifact validator: {type(exc).__name__}"],
        }
    return validate_artifacts()


def _mcp_safe_obj(value: Any, key_hint: str = "") -> Any:
    if _is_workspace_path_key(key_hint):
        return str(value)
    if _is_secret_key(key_hint):
        if isinstance(value, bool) or value is None:
            return value
        return "<REDACTED>"
    if isinstance(value, dict):
        return {str(sanitize_obj(key)): _mcp_safe_obj(item, str(key)) for key, item in value.items()}
    if isinstance(value, list):
        return [_mcp_safe_obj(item, key_hint) for item in value]
    if isinstance(value, tuple):
        return [_mcp_safe_obj(item, key_hint) for item in value]
    return sanitize_obj(value)


def _is_secret_key(key: str) -> bool:
    normalized = key.lower().replace("-", "_")
    if normalized.endswith("_present") or normalized.endswith("_ok"):
        return False
    return any(marker in normalized for marker in ("api_key", "authorization", "credential", "password", "secret", "token"))


def _is_workspace_path_key(key: str) -> bool:
    normalized = key.lower().replace("-", "_")
    return normalized in {"workspace_root", "expected_workspace_root"}


if __name__ == "__main__":
    raise SystemExit(main())
