#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import getpass
import hashlib
import hmac
import json
import os
import secrets
import sys
import time
import uuid
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
STATE_DIR = ROOT_DIR / ".jbt" / "lockctl"
CONFIG_FILE = STATE_DIR / "config.json"
STATE_FILE = STATE_DIR / "tokens.json"
EVENT_FILE = STATE_DIR / "events.jsonl"
TOKEN_VERSION = 1


def now_ts() -> int:
    return int(time.time())


def ensure_state_dir() -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)


def b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def b64url_decode(text: str) -> bytes:
    padding = "=" * (-len(text) % 4)
    return base64.urlsafe_b64decode(text + padding)


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def append_event(event: dict[str, Any]) -> None:
    ensure_state_dir()
    with EVENT_FILE.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")


def token_digest(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def password_to_hash(password: str, salt: bytes, iterations: int) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)


def prompt_password(confirm: bool = False) -> str:
    env_password = os.getenv("JBT_LOCK_PASSWORD")
    if env_password:
        if confirm:
            env_confirm = os.getenv("JBT_LOCK_PASSWORD_CONFIRM", env_password)
            if env_password != env_confirm:
                raise SystemExit("JBT_LOCK_PASSWORD_CONFIRM 与 JBT_LOCK_PASSWORD 不一致")
        return env_password

    first = getpass.getpass("请输入密码: ")
    if not confirm:
        return first

    second = getpass.getpass("请再次输入密码: ")
    if first != second:
        raise SystemExit("两次输入的密码不一致")
    return first


def load_config() -> dict[str, Any]:
    if not CONFIG_FILE.exists():
        raise SystemExit("锁控器尚未初始化，请先执行 bootstrap")
    return load_json(CONFIG_FILE, {})


def load_state() -> dict[str, Any]:
    return load_json(STATE_FILE, {"version": TOKEN_VERSION, "tokens": {}})


def save_state(state: dict[str, Any]) -> None:
    save_json(STATE_FILE, state)


def normalize_file_path(raw_path: str) -> str:
    raw = Path(raw_path)
    candidate = raw if raw.is_absolute() else ROOT_DIR / raw
    candidate = candidate.resolve(strict=False)

    try:
        relative = candidate.relative_to(ROOT_DIR.resolve())
    except ValueError as exc:
        raise SystemExit(f"文件超出 JBT 根目录范围: {raw_path}") from exc

    return relative.as_posix()


def normalize_files(raw_files: list[str]) -> list[str]:
    items = sorted({normalize_file_path(item) for item in raw_files})
    if not items:
        raise SystemExit("必须至少提供一个文件路径")
    return items


def encode_token(payload: dict[str, Any], signing_secret: str) -> str:
    header = {"alg": "HS256", "typ": "JBT_LOCK", "ver": TOKEN_VERSION}
    encoded_header = b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    encoded_payload = b64url_encode(json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{encoded_header}.{encoded_payload}".encode("utf-8")
    signature = hmac.new(signing_secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    return f"{encoded_header}.{encoded_payload}.{b64url_encode(signature)}"


def decode_token(token: str, signing_secret: str) -> dict[str, Any]:
    parts = token.split(".")
    if len(parts) != 3:
        raise SystemExit("Token 格式无效")

    encoded_header, encoded_payload, encoded_signature = parts
    signing_input = f"{encoded_header}.{encoded_payload}".encode("utf-8")
    expected_signature = hmac.new(signing_secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    actual_signature = b64url_decode(encoded_signature)

    if not hmac.compare_digest(expected_signature, actual_signature):
        raise SystemExit("Token 签名无效")

    payload = json.loads(b64url_decode(encoded_payload).decode("utf-8"))
    if payload.get("version") != TOKEN_VERSION:
        raise SystemExit("Token 版本不匹配")
    return payload


def verify_password(config: dict[str, Any], password: str) -> None:
    salt = base64.b64decode(config["password_salt"])
    expected = base64.b64decode(config["password_hash"])
    actual = password_to_hash(password, salt, int(config["password_iterations"]))
    if not hmac.compare_digest(actual, expected):
        raise SystemExit("密码验证失败")


def ensure_active_entry(state: dict[str, Any], payload: dict[str, Any], token: str) -> dict[str, Any]:
    token_id = payload["token_id"]
    entry = state["tokens"].get(token_id)
    if not entry:
        raise SystemExit("Token 未在本地状态中登记")

    if entry.get("token_sha256") != token_digest(token):
        raise SystemExit("Token 摘要不匹配")

    if entry.get("status") != "active":
        raise SystemExit(f"Token 当前不可用，状态为: {entry.get('status')}")

    if payload["expires_at"] < now_ts():
        entry["status"] = "expired"
        entry["expired_at"] = now_ts()
        save_state(state)
        raise SystemExit("Token 已过期")

    return entry


def cmd_bootstrap(args: argparse.Namespace) -> int:
    ensure_state_dir()
    if CONFIG_FILE.exists() and not args.force:
        raise SystemExit("锁控器已初始化；如需重建请显式传入 --force")

    password = prompt_password(confirm=True)
    salt = secrets.token_bytes(16)
    iterations = 240_000
    password_hash = password_to_hash(password, salt, iterations)
    signing_secret = secrets.token_urlsafe(48)

    config = {
        "version": TOKEN_VERSION,
        "owner": args.owner,
        "created_at": now_ts(),
        "password_iterations": iterations,
        "password_salt": base64.b64encode(salt).decode("ascii"),
        "password_hash": base64.b64encode(password_hash).decode("ascii"),
        "signing_secret": signing_secret,
    }
    save_json(CONFIG_FILE, config)
    save_state({"version": TOKEN_VERSION, "tokens": {}})

    append_event({
        "event": "bootstrap",
        "time": now_ts(),
        "owner": args.owner,
    })

    print(f"初始化完成: {CONFIG_FILE}")
    print("说明: 配置文件仅保存在本地 .jbt 目录，不进入 Git。")
    return 0


def cmd_issue(args: argparse.Namespace) -> int:
    ensure_state_dir()
    config = load_config()
    password = prompt_password(confirm=False)
    verify_password(config, password)

    allowed_files = normalize_files(args.files)
    issued_at = now_ts()
    expires_at = issued_at + args.ttl_minutes * 60
    token_id = f"tok-{uuid.uuid4()}"

    payload = {
        "version": TOKEN_VERSION,
        "token_id": token_id,
        "task_id": args.task,
        "agent": args.agent,
        "action": args.action,
        "allowed_files": allowed_files,
        "issued_at": issued_at,
        "expires_at": expires_at,
        "review_id": args.review_id,
        "notes": args.notes,
    }

    token = encode_token(payload, config["signing_secret"])
    state = load_state()
    state["tokens"][token_id] = {
        "task_id": args.task,
        "agent": args.agent,
        "action": args.action,
        "allowed_files": allowed_files,
        "issued_at": issued_at,
        "expires_at": expires_at,
        "review_id": args.review_id,
        "notes": args.notes,
        "status": "active",
        "token_sha256": token_digest(token),
    }
    save_state(state)

    append_event({
        "event": "issue",
        "time": issued_at,
        "token_id": token_id,
        "task_id": args.task,
        "agent": args.agent,
        "action": args.action,
        "allowed_files": allowed_files,
        "expires_at": expires_at,
    })

    print("Token 已生成")
    print(f"token_id: {token_id}")
    print(f"task_id: {args.task}")
    print(f"agent: {args.agent}")
    print(f"files: {', '.join(allowed_files)}")
    print(f"expires_at: {expires_at}")
    print()
    print(token)
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    config = load_config()
    payload = decode_token(args.token, config["signing_secret"])
    state = load_state()
    ensure_active_entry(state, payload, args.token)

    if payload["task_id"] != args.task:
        raise SystemExit("Token task_id 不匹配")
    if payload["agent"] != args.agent:
        raise SystemExit("Token agent 不匹配")
    if payload["action"] != args.action:
        raise SystemExit("Token action 不匹配")

    requested_files = normalize_files(args.files) if args.files else payload["allowed_files"]
    allowed_files = set(payload["allowed_files"])
    if not set(requested_files).issubset(allowed_files):
        raise SystemExit("请求文件超出 Token 白名单范围")

    print("Token 校验通过")
    print(f"token_id: {payload['token_id']}")
    print(f"task_id: {payload['task_id']}")
    print(f"agent: {payload['agent']}")
    print(f"action: {payload['action']}")
    print(f"allowed_files: {', '.join(payload['allowed_files'])}")
    print(f"expires_at: {payload['expires_at']}")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    state = load_state()
    tokens = state.get("tokens", {})
    rows = []
    current_time = now_ts()

    for token_id, entry in tokens.items():
        if args.agent and entry.get("agent") != args.agent:
            continue
        if args.task and entry.get("task_id") != args.task:
            continue
        status = entry.get("status", "unknown")
        if status == "active" and entry.get("expires_at", 0) < current_time:
            status = "expired"
        rows.append((token_id, entry.get("task_id"), entry.get("agent"), status))

    if not rows:
        print("没有匹配的 Token 记录")
        return 0

    for token_id, task_id, agent, status in rows:
        print(f"{token_id} | {task_id} | {agent} | {status}")
    return 0


def cmd_lockback(args: argparse.Namespace) -> int:
    config = load_config()
    payload = decode_token(args.token, config["signing_secret"])
    state = load_state()
    entry = ensure_active_entry(state, payload, args.token)

    entry["status"] = "locked" if args.result == "approved" else "rejected"
    entry["lockback_time"] = now_ts()
    entry["review_id"] = args.review_id or entry.get("review_id")
    entry["lockback_summary"] = args.summary
    save_state(state)

    append_event({
        "event": "lockback",
        "time": entry["lockback_time"],
        "token_id": payload["token_id"],
        "task_id": payload["task_id"],
        "agent": payload["agent"],
        "result": args.result,
        "review_id": args.review_id,
        "summary": args.summary,
    })

    print(f"Token 已锁回，状态: {entry['status']}")
    return 0


def cmd_revoke(args: argparse.Namespace) -> int:
    config = load_config()
    payload = decode_token(args.token, config["signing_secret"])
    state = load_state()
    entry = ensure_active_entry(state, payload, args.token)

    entry["status"] = "revoked"
    entry["revoked_time"] = now_ts()
    entry["revoke_reason"] = args.reason
    save_state(state)

    append_event({
        "event": "revoke",
        "time": entry["revoked_time"],
        "token_id": payload["token_id"],
        "task_id": payload["task_id"],
        "agent": payload["agent"],
        "reason": args.reason,
    })

    print("Token 已撤销")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="JBT 文件级 Token 锁控器")
    subparsers = parser.add_subparsers(dest="command", required=True)

    bootstrap_parser = subparsers.add_parser("bootstrap", help="初始化锁控器")
    bootstrap_parser.add_argument("--owner", default="Jay.S", help="锁控器所有者")
    bootstrap_parser.add_argument("--force", action="store_true", help="覆盖已有配置")
    bootstrap_parser.set_defaults(func=cmd_bootstrap)

    issue_parser = subparsers.add_parser("issue", help="生成任务 Token")
    issue_parser.add_argument("--task", required=True, help="任务 ID")
    issue_parser.add_argument("--agent", required=True, help="执行 Agent 中文名")
    issue_parser.add_argument("--action", default="edit", help="动作类型")
    issue_parser.add_argument("--ttl-minutes", type=int, default=30, help="Token 有效分钟数")
    issue_parser.add_argument("--review-id", default="", help="关联 review ID")
    issue_parser.add_argument("--notes", default="", help="附加说明")
    issue_parser.add_argument("--files", nargs="+", required=True, help="允许修改的文件白名单")
    issue_parser.set_defaults(func=cmd_issue)

    validate_parser = subparsers.add_parser("validate", help="校验任务 Token")
    validate_parser.add_argument("--token", required=True, help="待校验 Token")
    validate_parser.add_argument("--task", required=True, help="任务 ID")
    validate_parser.add_argument("--agent", required=True, help="执行 Agent 中文名")
    validate_parser.add_argument("--action", default="edit", help="动作类型")
    validate_parser.add_argument("--files", nargs="*", default=[], help="本次请求文件")
    validate_parser.set_defaults(func=cmd_validate)

    status_parser = subparsers.add_parser("status", help="查看本地 Token 状态")
    status_parser.add_argument("--task", default="", help="按任务过滤")
    status_parser.add_argument("--agent", default="", help="按 Agent 过滤")
    status_parser.set_defaults(func=cmd_status)

    lockback_parser = subparsers.add_parser("lockback", help="审核通过或拒绝后锁回 Token")
    lockback_parser.add_argument("--token", required=True, help="待锁回 Token")
    lockback_parser.add_argument("--result", choices=["approved", "rejected"], required=True, help="审核结果")
    lockback_parser.add_argument("--review-id", default="", help="review 记录 ID")
    lockback_parser.add_argument("--summary", default="", help="审核摘要")
    lockback_parser.set_defaults(func=cmd_lockback)

    revoke_parser = subparsers.add_parser("revoke", help="主动撤销 Token")
    revoke_parser.add_argument("--token", required=True, help="待撤销 Token")
    revoke_parser.add_argument("--reason", default="", help="撤销原因")
    revoke_parser.set_defaults(func=cmd_revoke)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())