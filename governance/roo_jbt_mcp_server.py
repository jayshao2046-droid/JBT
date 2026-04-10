#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
STATE_FILE = ROOT_DIR / ".jbt" / "lockctl" / "tokens.json"
SERVER_NAME = "jbt-governance"
SERVER_VERSION = "0.1.0"
DEFAULT_PROTOCOL_VERSION = "2025-11-25"

STARTUP_FILES = [
    "ATLAS_PROMPT.md",
    "docs/plans/ATLAS_MASTER_PLAN.md",
    "PROJECT_CONTEXT.md",
    "docs/prompts/总项目经理调度提示词.md",
    "docs/prompts/公共项目提示词.md",
]


def log(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


def now_epoch() -> int:
    return int(datetime.now().timestamp())


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_repo_path(raw_path: str) -> str:
    candidate = Path(raw_path)
    absolute = candidate if candidate.is_absolute() else ROOT_DIR / candidate
    resolved = absolute.resolve(strict=False)
    try:
        return resolved.relative_to(ROOT_DIR.resolve()).as_posix()
    except ValueError as exc:
        raise ValueError(f"Path is outside JBT root: {raw_path}") from exc


def load_active_tokens() -> dict[str, dict[str, Any]]:
    state = load_json(STATE_FILE, {"tokens": {}})
    tokens = state.get("tokens", {})
    active: dict[str, dict[str, Any]] = {}
    current = now_epoch()
    for token_id, entry in tokens.items():
        if entry.get("status") != "active":
            continue
        if int(entry.get("expires_at", 0)) < current:
            continue
        active[token_id] = entry
    return active


def format_token_summary(token_id: str, entry: dict[str, Any]) -> dict[str, Any]:
    return {
        "token_id": token_id,
        "task_id": entry.get("task_id"),
        "agent": entry.get("agent"),
        "action": entry.get("action"),
        "expires_at": entry.get("expires_at"),
        "allowed_files": entry.get("allowed_files", []),
        "notes": entry.get("notes", ""),
    }


def find_matching_tokens(
    files: list[str],
    task_id: str | None = None,
    agent: str | None = None,
    action: str | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    normalized_files = [normalize_repo_path(item) for item in files]
    exact_matches: list[dict[str, Any]] = []
    partial_matches: list[dict[str, Any]] = []
    other_agent_matches: list[dict[str, Any]] = []

    for token_id, entry in load_active_tokens().items():
        entry_task = entry.get("task_id")
        entry_agent = entry.get("agent")
        entry_action = entry.get("action")
        allowed_files = set(entry.get("allowed_files", []))
        covers_all = all(item in allowed_files for item in normalized_files)

        if task_id and entry_task != task_id:
            continue
        if action and entry_action != action:
            continue

        summary = format_token_summary(token_id, entry)
        if agent and entry_agent != agent:
            if covers_all:
                other_agent_matches.append(summary)
            continue

        if covers_all:
            exact_matches.append(summary)
        elif any(item in allowed_files for item in normalized_files):
            partial_matches.append(summary)

    return exact_matches, partial_matches, other_agent_matches


def tool_workflow_status(_: dict[str, Any]) -> dict[str, Any]:
    active_tokens = [format_token_summary(token_id, entry) for token_id, entry in load_active_tokens().items()]
    structured = {
        "repo_root": str(ROOT_DIR),
        "startup_files": STARTUP_FILES,
        "active_tokens": active_tokens,
        "rules": [
            "Atlas is the only business interface.",
            "Normal Roo implementation requires task, review, lock, and active file-level token.",
            "Read-only inspection may proceed before changes, but any write must return to pre-review and whitelist flow.",
            "Do not create a second prompt family outside ATLAS_PROMPT.md and docs/prompts.",
            "After each Roo batch, append a signed Roo entry to ATLAS_PROMPT.md only when that file is whitelisted.",
        ],
    }
    text = json.dumps(structured, ensure_ascii=False, indent=2)
    return {
        "content": [{"type": "text", "text": text}],
        "structuredContent": structured,
    }


def tool_check_token_access(arguments: dict[str, Any]) -> dict[str, Any]:
    files = arguments.get("files")
    if not isinstance(files, list) or not files:
        raise ValueError("files must be a non-empty array")

    task_id = arguments.get("task_id")
    agent = arguments.get("agent", "Roo")
    action = arguments.get("action", "edit")

    exact_matches, partial_matches, other_agent_matches = find_matching_tokens(files, task_id, agent, action)
    normalized_files = [normalize_repo_path(item) for item in files]
    structured = {
        "ok": bool(exact_matches),
        "requested_files": normalized_files,
        "task_id": task_id,
        "agent": agent,
        "action": action,
        "matches": exact_matches,
        "partial_matches": partial_matches,
        "other_agent_matches": other_agent_matches,
    }
    text = json.dumps(structured, ensure_ascii=False, indent=2)
    return {
        "content": [{"type": "text", "text": text}],
        "structuredContent": structured,
    }


def build_atlas_block(arguments: dict[str, Any]) -> str:
    task_id = arguments["task_id"]
    agent = arguments.get("agent", "Roo")
    entry_type = arguments.get("entry_type", "implementation")
    summary = arguments["summary"].strip()
    verification = arguments.get("verification") or []
    risks = arguments.get("risks") or []
    next_steps = arguments.get("next_steps") or []

    if not summary:
        raise ValueError("summary must not be empty")

    sections = [
        f"【签名】{agent}",
        f"【时间】{now_text()}",
        "【设备】MacBook",
        f"【任务】{task_id}",
        f"【类型】{entry_type}",
        "【摘要】",
        f"- {summary}",
    ]

    def extend_section(title: str, values: list[str]) -> None:
        if not values:
            return
        sections.append(title)
        for value in values:
            if value and isinstance(value, str):
                sections.append(f"- {value}")

    extend_section("【验证】", verification)
    extend_section("【风险】", risks)
    extend_section("【下一步】", next_steps)
    return "\n".join(sections)


def tool_append_atlas_log(arguments: dict[str, Any]) -> dict[str, Any]:
    task_id = arguments.get("task_id")
    if not isinstance(task_id, str) or not task_id.strip():
        raise ValueError("task_id is required")

    agent = arguments.get("agent", "Roo")
    if not isinstance(agent, str) or not agent.strip():
        raise ValueError("agent must be a non-empty string")

    exact_matches, partial_matches, other_agent_matches = find_matching_tokens(
        ["ATLAS_PROMPT.md"],
        task_id=task_id,
        agent=agent,
        action="edit",
    )
    if not exact_matches:
        structured = {
            "ok": False,
            "reason": "No active token covers ATLAS_PROMPT.md for this task and agent.",
            "task_id": task_id,
            "agent": agent,
            "matches": exact_matches,
            "partial_matches": partial_matches,
            "other_agent_matches": other_agent_matches,
        }
        return {
            "content": [{"type": "text", "text": json.dumps(structured, ensure_ascii=False, indent=2)}],
            "structuredContent": structured,
            "isError": True,
        }

    atlas_path = ROOT_DIR / "ATLAS_PROMPT.md"
    existing = atlas_path.read_text(encoding="utf-8")
    block = build_atlas_block(arguments)
    separator = "\n\n" if existing.endswith("\n") else "\n\n"
    atlas_path.write_text(existing.rstrip("\n") + separator + block + "\n", encoding="utf-8")

    structured = {
        "ok": True,
        "task_id": task_id,
        "agent": agent,
        "path": "ATLAS_PROMPT.md",
        "used_token": exact_matches[0]["token_id"],
        "appended_block": block,
    }
    return {
        "content": [{"type": "text", "text": json.dumps(structured, ensure_ascii=False, indent=2)}],
        "structuredContent": structured,
    }


TOOLS: dict[str, dict[str, Any]] = {
    "workflow_status": {
        "title": "JBT Workflow Status",
        "description": "Return the JBT startup chain, active tokens, and the core governance rules Roo must follow.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
        "handler": tool_workflow_status,
    },
    "check_token_access": {
        "title": "Check Token Access",
        "description": "Check whether an active file-level token covers the requested task, agent, action, and files.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task_id": {"type": "string"},
                "agent": {"type": "string"},
                "action": {"type": "string"},
                "files": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 1,
                },
            },
            "required": ["files"],
            "additionalProperties": False,
        },
        "handler": tool_check_token_access,
    },
    "append_atlas_log": {
        "title": "Append Atlas Log",
        "description": "Append a signed Roo batch summary to ATLAS_PROMPT.md only when the current task and agent have active token access to that file.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task_id": {"type": "string"},
                "agent": {"type": "string"},
                "entry_type": {"type": "string"},
                "summary": {"type": "string"},
                "verification": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "risks": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "next_steps": {
                    "type": "array",
                    "items": {"type": "string"},
                },
            },
            "required": ["task_id", "summary"],
            "additionalProperties": False,
        },
        "handler": tool_append_atlas_log,
    },
}


class McpServer:
    def __init__(self) -> None:
        self.protocol_version = DEFAULT_PROTOCOL_VERSION

    def send(self, payload: dict[str, Any]) -> None:
        sys.stdout.write(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n")
        sys.stdout.flush()

    def send_result(self, request_id: Any, result: dict[str, Any]) -> None:
        self.send({"jsonrpc": "2.0", "id": request_id, "result": result})

    def send_error(self, request_id: Any, code: int, message: str) -> None:
        self.send({"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}})

    def handle_initialize(self, request_id: Any, params: dict[str, Any]) -> None:
        self.protocol_version = params.get("protocolVersion") or DEFAULT_PROTOCOL_VERSION
        result = {
            "protocolVersion": self.protocol_version,
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
            "instructions": (
                "Use check_token_access before any write and use append_atlas_log only when "
                "ATLAS_PROMPT.md is covered by the current task token."
            ),
        }
        self.send_result(request_id, result)

    def handle_tools_list(self, request_id: Any) -> None:
        tools = []
        for name, definition in TOOLS.items():
            tools.append(
                {
                    "name": name,
                    "title": definition["title"],
                    "description": definition["description"],
                    "inputSchema": definition["inputSchema"],
                }
            )
        self.send_result(request_id, {"tools": tools})

    def handle_tools_call(self, request_id: Any, params: dict[str, Any]) -> None:
        tool_name = params.get("name")
        if tool_name not in TOOLS:
            self.send_error(request_id, -32601, f"Unknown tool: {tool_name}")
            return

        arguments = params.get("arguments") or {}
        if not isinstance(arguments, dict):
            self.send_error(request_id, -32602, "Tool arguments must be an object")
            return

        try:
            result = TOOLS[tool_name]["handler"](arguments)
        except ValueError as exc:
            result = {
                "content": [{"type": "text", "text": str(exc)}],
                "structuredContent": {"ok": False, "error": str(exc)},
                "isError": True,
            }
        except Exception as exc:  # pragma: no cover
            log(f"Tool failure in {tool_name}: {exc}")
            result = {
                "content": [{"type": "text", "text": f"Internal server error: {exc}"}],
                "structuredContent": {"ok": False, "error": str(exc)},
                "isError": True,
            }
        self.send_result(request_id, result)

    def handle_request(self, request: dict[str, Any]) -> None:
        if request.get("jsonrpc") != "2.0":
            self.send_error(request.get("id"), -32600, "Invalid JSON-RPC version")
            return

        method = request.get("method")
        request_id = request.get("id")
        params = request.get("params") or {}

        if method == "initialize":
            self.handle_initialize(request_id, params if isinstance(params, dict) else {})
            return
        if method == "ping":
            self.send_result(request_id, {})
            return
        if method == "tools/list":
            self.handle_tools_list(request_id)
            return
        if method == "tools/call":
            self.handle_tools_call(request_id, params if isinstance(params, dict) else {})
            return
        if method in {"notifications/initialized", "initialized"}:
            return

        if request_id is not None:
            self.send_error(request_id, -32601, f"Method not found: {method}")

    def serve_forever(self) -> int:
        for raw_line in sys.stdin:
            line = raw_line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError as exc:
                self.send_error(None, -32700, f"Parse error: {exc}")
                continue

            try:
                if isinstance(payload, list):
                    for item in payload:
                        if isinstance(item, dict):
                            self.handle_request(item)
                        else:
                            self.send_error(None, -32600, "Invalid request object in batch")
                elif isinstance(payload, dict):
                    self.handle_request(payload)
                else:
                    self.send_error(None, -32600, "Invalid request")
            except Exception as exc:  # pragma: no cover
                log(f"Unhandled server error: {exc}")
                self.send_error(payload.get("id") if isinstance(payload, dict) else None, -32603, str(exc))
        return 0


def main() -> int:
    return McpServer().serve_forever()


if __name__ == "__main__":
    raise SystemExit(main())