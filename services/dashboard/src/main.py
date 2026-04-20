from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import secrets
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from pydantic import BaseModel

logger = logging.getLogger(__name__)

SERVICE_NAME = "jbt-dashboard"
SERVICE_VERSION = "1.0.0"
SERVICE_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = SERVICE_ROOT / "runtime" / "dashboard.db"

# API Key 认证（服务间调用）
_DASHBOARD_API_KEY = os.environ.get("DASHBOARD_API_KEY", "")
_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
_session_header = APIKeyHeader(name="Authorization", auto_error=False)

# 不需要 API Key 的路径（包含用户/认证相关路径）
_PUBLIC_PATHS = {
    "/health",
    "/api/v1/health",
    "/api/v1/auth/login",
    "/api/v1/auth/logout",
    "/api/v1/auth/me",
}


async def _verify_api_key(request: Request, api_key: Optional[str] = Depends(_api_key_header)) -> None:
    """服务间 API Key 认证（用户认证路径豁免）"""
    path = request.url.path
    # 认证/用户管理路径走 session 认证，不走 API Key
    if path in _PUBLIC_PATHS or path.startswith("/api/v1/users") or path.startswith("/api/v1/auth") or path.startswith("/api/v1/trading"):
        return

    env = os.environ.get("JBT_ENV", "development").lower()
    if not _DASHBOARD_API_KEY:
        if env == "production":
            raise HTTPException(status_code=503, detail="DASHBOARD_API_KEY not configured")
        logger.warning("DASHBOARD_API_KEY not configured - dev mode")
        return

    if not api_key or not hmac.compare_digest(api_key, _DASHBOARD_API_KEY):
        raise HTTPException(status_code=403, detail="invalid or missing API key")


app = FastAPI(title="JBT Dashboard Service", version=SERVICE_VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3005", "http://127.0.0.1:3005"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── 数据库初始化 ──────────────────────────────────────────
def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            token TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    # Migration: add permissions column if it doesn't exist yet
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN permissions TEXT NOT NULL DEFAULT '[]'")
    except sqlite3.OperationalError:
        pass  # column already exists

    # 交易时段配置表（每天3个期货时段）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trading_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            label TEXT NOT NULL,
            enabled INTEGER NOT NULL DEFAULT 1,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            sort_order INTEGER NOT NULL DEFAULT 0,
            updated_at TEXT NOT NULL
        )
    """)

    # 交易全局配置
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trading_config (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)

    # 交易日历（节假日 / 补班日 / 临时休市）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trading_calendar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL UNIQUE,
            type TEXT NOT NULL DEFAULT 'holiday',
            label TEXT NOT NULL DEFAULT '',
            note TEXT NOT NULL DEFAULT '',
            trading_enabled INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL
        )
    """)
    # 迁移：为已存在的表补 trading_enabled 列
    try:
        cursor.execute("ALTER TABLE trading_calendar ADD COLUMN trading_enabled INTEGER NOT NULL DEFAULT 0")
    except sqlite3.OperationalError:
        pass  # column already exists

    # 初始化默认期货三时段
    cursor.execute("SELECT COUNT(*) FROM trading_sessions")
    if cursor.fetchone()[0] == 0:
        now_str = datetime.now().isoformat()
        default_sessions = [
            ("night",   "夜盘",   1, "21:00", "23:00", 0, now_str),
            ("morning", "上午盘", 1, "09:00", "11:30", 1, now_str),
            ("afternoon","下午盘",1, "13:30", "15:00", 2, now_str),
        ]
        cursor.executemany(
            "INSERT INTO trading_sessions (name,label,enabled,start_time,end_time,sort_order,updated_at) VALUES (?,?,?,?,?,?,?)",
            default_sessions
        )

    # 初始化默认全局配置
    defaults = {
        "auto_trading_enabled": "true",
        "pre_market_minutes": "30",
        "post_market_enabled": "true",
        "pre_market_enabled": "true",
        "timezone": "Asia/Shanghai",
    }
    for k, v in defaults.items():
        cursor.execute("INSERT OR IGNORE INTO trading_config (key,value,updated_at) VALUES (?,?,?)",
                       (k, v, datetime.now().isoformat()))

    # 预置 2026 年中国大陆期货市场节假日（仅首次）
    cursor.execute("SELECT COUNT(*) FROM trading_calendar WHERE date LIKE '2026-%'")
    if cursor.fetchone()[0] == 0:
        now_str = datetime.now().isoformat()
        # (date, type, label, note, trading_enabled)
        cn_2026 = [
            # 元旦
            ("2026-01-01", "holiday", "元旦", "", 0),
            ("2026-01-02", "holiday", "元旦假期", "", 0),
            ("2026-01-03", "holiday", "元旦假期", "", 0),
            # 春节（2026年CNY = 2月17日）
            ("2026-02-15", "holiday", "春节假期", "", 0),
            ("2026-02-16", "holiday", "春节假期", "", 0),
            ("2026-02-17", "holiday", "春节（大年初一）", "", 0),
            ("2026-02-18", "holiday", "春节假期", "", 0),
            ("2026-02-19", "holiday", "春节假期", "", 0),
            ("2026-02-20", "holiday", "春节假期", "", 0),
            ("2026-02-21", "holiday", "春节假期", "", 0),
            # 春节补班
            ("2026-02-08", "workday", "春节前补班", "", 1),
            ("2026-02-28", "workday", "春节后补班", "", 1),
            # 清明节
            ("2026-04-04", "holiday", "清明节", "", 0),
            ("2026-04-05", "holiday", "清明节假期", "", 0),
            ("2026-04-06", "holiday", "清明节假期", "", 0),
            # 劳动节
            ("2026-05-01", "holiday", "劳动节", "", 0),
            ("2026-05-02", "holiday", "劳动节假期", "", 0),
            ("2026-05-03", "holiday", "劳动节假期", "", 0),
            ("2026-05-04", "holiday", "劳动节假期", "", 0),
            ("2026-05-05", "holiday", "劳动节假期", "", 0),
            # 劳动节补班
            ("2026-04-26", "workday", "劳动节前补班", "", 1),
            # 端午节（2026年6月20日）
            ("2026-06-19", "holiday", "端午节假期", "", 0),
            ("2026-06-20", "holiday", "端午节", "", 0),
            ("2026-06-21", "holiday", "端午节假期", "", 0),
            # 中秋节+国庆节
            ("2026-10-01", "holiday", "国庆节", "", 0),
            ("2026-10-02", "holiday", "国庆节假期", "", 0),
            ("2026-10-03", "holiday", "国庆节假期", "", 0),
            ("2026-10-04", "holiday", "中秋节", "", 0),
            ("2026-10-05", "holiday", "国庆节假期", "", 0),
            ("2026-10-06", "holiday", "国庆节假期", "", 0),
            ("2026-10-07", "holiday", "国庆节假期", "", 0),
            # 国庆补班
            ("2026-09-27", "workday", "国庆节前补班", "", 1),
            ("2026-10-10", "workday", "国庆节后补班", "", 1),
        ]
        cursor.executemany(
            "INSERT OR IGNORE INTO trading_calendar (date,type,label,note,trading_enabled,created_at) VALUES (?,?,?,?,?,?)",
            [(d, t, l, n, te, now_str) for d, t, l, n, te in cn_2026]
        )

    # 通知配置表（每个服务一行）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notification_configs (
            service TEXT PRIMARY KEY,
            feishu_webhook TEXT NOT NULL DEFAULT '',
            feishu_enabled INTEGER NOT NULL DEFAULT 1,
            smtp_host TEXT NOT NULL DEFAULT '',
            smtp_port INTEGER NOT NULL DEFAULT 465,
            smtp_username TEXT NOT NULL DEFAULT '',
            smtp_password TEXT NOT NULL DEFAULT '',
            smtp_to_addrs TEXT NOT NULL DEFAULT '',
            smtp_enabled INTEGER NOT NULL DEFAULT 0,
            updated_at TEXT NOT NULL DEFAULT ''
        )
    """)

    # 通知规则表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notification_rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            service TEXT NOT NULL,
            name TEXT NOT NULL,
            rule_type TEXT NOT NULL,
            color TEXT NOT NULL DEFAULT 'turquoise',
            content_template TEXT NOT NULL DEFAULT '',
            enabled INTEGER NOT NULL DEFAULT 1,
            feishu_enabled INTEGER NOT NULL DEFAULT 1,
            smtp_enabled INTEGER NOT NULL DEFAULT 1,
            sort_order INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    # 迁移：为已存在的数据库加上新列（幂等）
    for col, default in [("feishu_enabled", 1), ("smtp_enabled", 1)]:
        try:
            cursor.execute(f"ALTER TABLE notification_rules ADD COLUMN {col} INTEGER NOT NULL DEFAULT {default}")
        except sqlite3.OperationalError:
            pass  # 列已存在

    # 种子：各服务默认通知配置
    cursor.execute("SELECT COUNT(*) FROM notification_configs")
    if cursor.fetchone()[0] == 0:
        now_str = datetime.now().isoformat()
        default_services = ["sim-trading", "data", "decision", "backtest"]
        cursor.executemany(
            "INSERT OR IGNORE INTO notification_configs (service, updated_at) VALUES (?, ?)",
            [(s, now_str) for s in default_services]
        )

    # 种子：默认通知规则（首次初始化）
    cursor.execute("SELECT COUNT(*) FROM notification_rules")
    if cursor.fetchone()[0] == 0:
        now_str = datetime.now().isoformat()
        default_rules = [
            # sim-trading
            ("sim-trading", "CTP 断线告警",   "alarm_p1", "orange",    "CTP 连接中断: {reason}",        1, 1, 1, 0),
            ("sim-trading", "强制平仓告警",   "alarm_p0", "red",       "触发强制平仓: {reason}\n持仓: {positions}", 1, 1, 1, 1),
            ("sim-trading", "风控告警",       "alarm_p2", "yellow",    "风控预警: {rule} 当前值 {value}", 1, 1, 1, 2),
            ("sim-trading", "成交回报",       "trade",    "grey",      "订单成交: {symbol} {direction} {volume}手 @ {price}", 1, 1, 0, 3),
            ("sim-trading", "系统启停通知",   "notify",   "turquoise", "服务 {action}: {service_name} at {time}", 1, 1, 0, 4),
            ("sim-trading", "日报汇总",       "info",     "blue",      "今日交易汇总\n盈亏: {pnl}\n成交: {trades}笔\n胜率: {win_rate}", 1, 1, 1, 5),
            # data
            ("data", "采集失败告警",  "alarm_p1", "orange",    "数据采集器异常: {collector}\n错误: {error}",   1, 1, 1, 0),
            ("data", "存储空间预警",  "alarm_p2", "yellow",    "存储空间不足: {path} 剩余 {free_gb}GB",       1, 1, 0, 1),
            ("data", "新闻推送",      "news",     "wathet",    "[{source}] {title}\n{summary}",               1, 1, 0, 2),
            ("data", "采集器状态",   "notify",   "turquoise", "采集器 {name} 状态: {status}\n延迟: {delay}s",1, 1, 0, 3),
            ("data", "日报汇总",      "info",     "blue",      "数据采集日报\n成功: {ok}条 失败: {fail}条",   1, 1, 1, 4),
            # decision
            ("decision", "策略信号生成", "info",     "blue",      "信号生成: {strategy} {symbol} {direction}\n置信度: {confidence}", 1, 1, 0, 0),
            ("decision", "LLM 分析完成", "info",     "blue",      "研究员分析报告: {title}\n评分: {score}",     1, 1, 0, 1),
            ("decision", "风控告警",     "alarm_p1", "orange",    "决策风控预警: {reason}\n触发规则: {rule}",   1, 1, 1, 2),
            ("decision", "信号待审批",   "notify",   "turquoise", "待审批信号: {strategy} {symbol}\n强度: {strength}", 1, 1, 0, 3),
            # backtest
            ("backtest", "回测完成",     "notify", "turquoise", "回测完成: {task_name}\n收益率: {return_pct}% 最大回撤: {max_dd}%", 1, 1, 0, 0),
            ("backtest", "回测失败",     "alarm_p1", "orange",  "回测异常: {task_name}\n错误: {error}",         1, 1, 0, 1),
            ("backtest", "参数优化完成", "info",   "blue",      "参数优化完成: {task_name}\n最优参数: {params}", 1, 1, 0, 2),
        ]
        cursor.executemany(
            "INSERT INTO notification_rules (service,name,rule_type,color,content_template,enabled,feishu_enabled,smtp_enabled,sort_order,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            [(s, n, rt, c, ct, e, fe, se, so, now_str, now_str) for s, n, rt, c, ct, e, fe, se, so in default_rules]
        )


    cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
    if cursor.fetchone()[0] == 0:
        admin_hash = hashlib.sha256("admin123".encode()).hexdigest()
        now = datetime.now().isoformat()
        cursor.execute(
            "INSERT INTO users (username, password_hash, role, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            ("admin", admin_hash, "admin", now, now)
        )

    conn.commit()
    conn.close()


@app.on_event("startup")
async def startup_event():
    init_db()
    logger.info(f"{SERVICE_NAME} v{SERVICE_VERSION} started")


# ── Session 辅助函数 ──────────────────────────────────────────
def create_session(user_id: int) -> str:
    """创建 session token，有效期 30 天"""
    token = secrets.token_urlsafe(32)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now = datetime.now()
    expires = now + timedelta(days=30)
    cursor.execute(
        "INSERT INTO sessions (token, user_id, created_at, expires_at) VALUES (?, ?, ?, ?)",
        (token, user_id, now.isoformat(), expires.isoformat()),
    )
    conn.commit()
    conn.close()
    return token


def get_session_user(token: str) -> Optional[dict]:
    """通过 token 获取当前用户，token 过期或不存在返回 None"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """SELECT u.id, u.username, u.role, u.created_at, u.permissions
           FROM sessions s JOIN users u ON s.user_id = u.id
           WHERE s.token = ? AND s.expires_at > ?""",
        (token, datetime.now().isoformat()),
    )
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    return {
        "id": row[0], "username": row[1], "role": row[2],
        "created_at": row[3], "permissions": json.loads(row[4] or '[]'),
    }


def delete_session(token: str) -> None:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM sessions WHERE token = ?", (token,))
    conn.commit()
    conn.close()


# ── 认证依赖 ──────────────────────────────────────────
async def get_current_user(authorization: Optional[str] = Depends(_session_header)) -> dict:
    """从 Authorization: Bearer <token> 头中获取当前用户"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未认证，请先登录")
    token = authorization[7:]
    user = get_session_user(token)
    if not user:
        raise HTTPException(status_code=401, detail="会话已过期，请重新登录")
    return user


async def require_admin(user: dict = Depends(get_current_user)) -> dict:
    """要求管理员身份"""
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return user


# ── API Models ──────────────────────────────────────────
class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    success: bool
    token: Optional[str] = None
    user: Optional[dict] = None
    message: Optional[str] = None


class User(BaseModel):
    id: int
    username: str
    role: str
    created_at: str
    permissions: list[str] = []


class CreateUserRequest(BaseModel):
    username: str
    password: str
    role: str = "user"
    permissions: list[str] = []


class UpdatePermissionsRequest(BaseModel):
    permissions: list[str]


class UpdatePasswordRequest(BaseModel):
    old_password: Optional[str] = None
    new_password: str


class UpdateUserRequest(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None


# ── 认证端点 ──────────────────────────────────────────
@app.post("/api/v1/auth/login", response_model=LoginResponse)
async def login(req: LoginRequest):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    password_hash = hashlib.sha256(req.password.encode()).hexdigest()
    cursor.execute(
        "SELECT id, username, role, created_at FROM users WHERE LOWER(username) = LOWER(?) AND password_hash = ?",
        (req.username, password_hash)
    )

    row = cursor.fetchone()
    conn.close()

    if not row:
        return LoginResponse(success=False, message="用户名或密码错误")

    token = create_session(row[0])

    return LoginResponse(
        success=True,
        token=token,
        user={
            "id": row[0],
            "username": row[1],
            "role": row[2],
            "created_at": row[3],
        }
    )


@app.get("/api/v1/auth/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    """获取当前登录用户信息"""
    return current_user


@app.post("/api/v1/auth/logout")
async def logout(authorization: Optional[str] = Depends(_session_header)):
    """登出，使当前 session 失效"""
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
        delete_session(token)
    return {"success": True}


# ── 用户管理端点 ──────────────────────────────────────────
@app.get("/api/v1/users", response_model=list[User])
async def list_users(admin: dict = Depends(require_admin)):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, role, created_at, permissions FROM users ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [
        User(id=r[0], username=r[1], role=r[2], created_at=r[3], permissions=json.loads(r[4] or '[]'))
        for r in rows
    ]


@app.post("/api/v1/users", response_model=User)
async def create_user(req: CreateUserRequest, admin: dict = Depends(require_admin)):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 检查用户名是否已存在
    cursor.execute("SELECT COUNT(*) FROM users WHERE username = ?", (req.username,))
    if cursor.fetchone()[0] > 0:
        conn.close()
        raise HTTPException(status_code=400, detail="用户名已存在")

    if len(req.password) < 6:
        conn.close()
        raise HTTPException(status_code=400, detail="密码长度不能少于6位")

    password_hash = hashlib.sha256(req.password.encode()).hexdigest()
    permissions_json = json.dumps(req.permissions)
    now = datetime.now().isoformat()

    cursor.execute(
        "INSERT INTO users (username, password_hash, role, permissions, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
        (req.username, password_hash, req.role, permissions_json, now, now)
    )
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return User(id=user_id, username=req.username, role=req.role, created_at=now, permissions=req.permissions)


@app.put("/api/v1/users/{user_id}")
async def update_user(user_id: int, req: UpdateUserRequest, admin: dict = Depends(require_admin)):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    updates = []
    params = []

    if req.username:
        # 检查新用户名是否冲突
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = ? AND id != ?", (req.username, user_id))
        if cursor.fetchone()[0] > 0:
            conn.close()
            raise HTTPException(status_code=400, detail="用户名已存在")
        updates.append("username = ?")
        params.append(req.username)

    if req.password:
        if len(req.password) < 6:
            conn.close()
            raise HTTPException(status_code=400, detail="密码长度不能少于6位")
        updates.append("password_hash = ?")
        params.append(hashlib.sha256(req.password.encode()).hexdigest())

    if req.role:
        # 不能降级最后一个管理员
        if req.role != "admin":
            cursor.execute("SELECT role FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            if row and row[0] == "admin":
                cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
                if cursor.fetchone()[0] <= 1:
                    conn.close()
                    raise HTTPException(status_code=400, detail="不能降级最后一个管理员")
        updates.append("role = ?")
        params.append(req.role)

    if not updates:
        conn.close()
        raise HTTPException(status_code=400, detail="没有需要更新的字段")

    updates.append("updated_at = ?")
    params.append(datetime.now().isoformat())
    params.append(user_id)

    cursor.execute(f"UPDATE users SET {', '.join(updates)} WHERE id = ?", params)
    conn.commit()
    conn.close()

    return {"success": True}


@app.delete("/api/v1/users/{user_id}")
async def delete_user(user_id: int, admin: dict = Depends(require_admin)):
    # 不能删除自己
    if user_id == admin["id"]:
        raise HTTPException(status_code=400, detail="不能删除自己的账户")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 不允许删除最后一个管理员
    cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
    admin_count = cursor.fetchone()[0]

    cursor.execute("SELECT role FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="用户不存在")

    if row[0] == "admin" and admin_count <= 1:
        conn.close()
        raise HTTPException(status_code=400, detail="不能删除最后一个管理员账户")

    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()

    return {"success": True}


@app.post("/api/v1/users/{user_id}/password")
async def change_password(user_id: int, req: UpdatePasswordRequest, current_user: dict = Depends(get_current_user)):
    """修改密码：管理员可直接修改任意用户；普通用户只能改自己的（需验证旧密码）"""
    is_admin = current_user["role"] == "admin"
    is_self = user_id == current_user["id"]

    if not is_admin and not is_self:
        raise HTTPException(status_code=403, detail="无权修改其他用户的密码")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 普通用户修改自己密码需要验证旧密码
    if is_self and not is_admin:
        if not req.old_password:
            conn.close()
            raise HTTPException(status_code=400, detail="需要提供当前密码")
        old_hash = hashlib.sha256(req.old_password.encode()).hexdigest()
        cursor.execute("SELECT COUNT(*) FROM users WHERE id = ? AND password_hash = ?", (user_id, old_hash))
        if cursor.fetchone()[0] == 0:
            conn.close()
            raise HTTPException(status_code=400, detail="当前密码错误")

    if len(req.new_password) < 6:
        conn.close()
        raise HTTPException(status_code=400, detail="密码长度不能少于6位")

    new_hash = hashlib.sha256(req.new_password.encode()).hexdigest()
    cursor.execute(
        "UPDATE users SET password_hash = ?, updated_at = ? WHERE id = ?",
        (new_hash, datetime.now().isoformat(), user_id)
    )
    conn.commit()
    conn.close()

    return {"success": True}


@app.get("/api/v1/users/{user_id}/permissions")
async def get_user_permissions(user_id: int, admin: dict = Depends(require_admin)):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT permissions FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="用户不存在")
    return {"permissions": json.loads(row[0] or '[]')}


@app.put("/api/v1/users/{user_id}/permissions")
async def update_user_permissions(
    user_id: int, req: UpdatePermissionsRequest, admin: dict = Depends(require_admin)
):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users WHERE id = ?", (user_id,))
    if cursor.fetchone()[0] == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="用户不存在")
    cursor.execute(
        "UPDATE users SET permissions = ?, updated_at = ? WHERE id = ?",
        (json.dumps(req.permissions), datetime.now().isoformat(), user_id),
    )
    conn.commit()
    conn.close()
    return {"success": True, "permissions": req.permissions}


@app.get("/api/v1/trading/sessions")
async def get_trading_sessions(current_user: dict = Depends(get_current_user)):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id,name,label,enabled,start_time,end_time,sort_order FROM trading_sessions ORDER BY sort_order")
    rows = cursor.fetchall()
    conn.close()
    return [{"id":r[0],"name":r[1],"label":r[2],"enabled":bool(r[3]),"start_time":r[4],"end_time":r[5],"sort_order":r[6]} for r in rows]


@app.put("/api/v1/trading/sessions/{session_id}")
async def update_trading_session(session_id: int, req: dict, admin: dict = Depends(require_admin)):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM trading_sessions WHERE id=?", (session_id,))
    if cursor.fetchone()[0] == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="时段不存在")
    updates, params = [], []
    for field in ("label","enabled","start_time","end_time"):
        if field in req:
            updates.append(f"{field}=?")
            params.append(int(req[field]) if field == "enabled" else req[field])
    if not updates:
        conn.close()
        raise HTTPException(status_code=400, detail="无可更新字段")
    updates.append("updated_at=?")
    params.append(datetime.now().isoformat())
    params.append(session_id)
    cursor.execute(f"UPDATE trading_sessions SET {','.join(updates)} WHERE id=?", params)
    conn.commit()
    conn.close()
    return {"success": True}


@app.get("/api/v1/trading/config")
async def get_trading_config(current_user: dict = Depends(get_current_user)):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT key,value FROM trading_config")
    rows = cursor.fetchall()
    conn.close()
    return {r[0]: r[1] for r in rows}


@app.put("/api/v1/trading/config")
async def update_trading_config(req: dict, admin: dict = Depends(require_admin)):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    for k, v in req.items():
        cursor.execute("INSERT OR REPLACE INTO trading_config (key,value,updated_at) VALUES (?,?,?)", (k, str(v), now))
    conn.commit()
    conn.close()
    return {"success": True}


@app.get("/api/v1/trading/calendar")
async def get_trading_calendar(year: Optional[int] = None, current_user: dict = Depends(get_current_user)):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    if year:
        cursor.execute("SELECT id,date,type,label,note,trading_enabled,created_at FROM trading_calendar WHERE date LIKE ? ORDER BY date", (f"{year}-%",))
    else:
        cursor.execute("SELECT id,date,type,label,note,trading_enabled,created_at FROM trading_calendar ORDER BY date DESC LIMIT 200")
    rows = cursor.fetchall()
    conn.close()
    return [{"id":r[0],"date":r[1],"type":r[2],"label":r[3],"note":r[4],"trading_enabled":bool(r[5]),"created_at":r[6]} for r in rows]


class CalendarEntryRequest(BaseModel):
    date: str
    type: str = "holiday"   # holiday | workday | early_close
    label: str = ""
    note: str = ""
    trading_enabled: bool = False


@app.post("/api/v1/trading/calendar")
async def add_calendar_entry(req: CalendarEntryRequest, admin: dict = Depends(require_admin)):
    import re
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", req.date):
        raise HTTPException(status_code=400, detail="日期格式必须为 YYYY-MM-DD")
    if req.type not in ("holiday", "workday", "early_close"):
        raise HTTPException(status_code=400, detail="type 必须为 holiday/workday/early_close")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO trading_calendar (date,type,label,note,trading_enabled,created_at) VALUES (?,?,?,?,?,?)",
            (req.date, req.type, req.label, req.note, 1 if req.trading_enabled else 0, datetime.now().isoformat())
        )
        entry_id = cursor.lastrowid
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="该日期已存在日历条目")
    conn.close()
    return {"id": entry_id, "date": req.date, "type": req.type, "label": req.label, "note": req.note, "trading_enabled": req.trading_enabled}


@app.put("/api/v1/trading/calendar/{entry_id}")
async def update_calendar_entry(entry_id: int, req: CalendarEntryRequest, admin: dict = Depends(require_admin)):
    import re
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", req.date):
        raise HTTPException(status_code=400, detail="日期格式必须为 YYYY-MM-DD")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM trading_calendar WHERE id=?", (entry_id,))
    if cursor.fetchone()[0] == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="条目不存在")
    cursor.execute(
        "UPDATE trading_calendar SET date=?,type=?,label=?,note=?,trading_enabled=? WHERE id=?",
        (req.date, req.type, req.label, req.note, 1 if req.trading_enabled else 0, entry_id)
    )
    conn.commit()
    conn.close()
    return {"success": True}


@app.delete("/api/v1/trading/calendar/{entry_id}")
async def delete_calendar_entry(entry_id: int, admin: dict = Depends(require_admin)):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM trading_calendar WHERE id=?", (entry_id,))
    conn.commit()
    conn.close()
    return {"success": True}


@app.get("/health")
async def health():
    return {"status": "healthy", "service": SERVICE_NAME, "version": SERVICE_VERSION}


# ── 通知配置 API ──────────────────────────────────────────

_SERVICE_LABELS = {
    "sim-trading": "模拟交易",
    "data":        "数据服务",
    "decision":    "决策引擎",
    "backtest":    "回测系统",
}

class NotificationConfigRequest(BaseModel):
    feishu_webhook: str = ""
    feishu_enabled: bool = True
    smtp_host: str = ""
    smtp_port: int = 465
    smtp_username: str = ""
    smtp_password: str = ""   # 空字符串 = 保留原密码
    smtp_to_addrs: str = ""
    smtp_enabled: bool = False


class NotificationRuleRequest(BaseModel):
    service: str
    name: str
    rule_type: str   # alarm_p0/alarm_p1/alarm_p2/trade/info/news/notify
    color: str = "turquoise"
    content_template: str = ""
    enabled: bool = True
    feishu_enabled: bool = True
    smtp_enabled: bool = True


def _row_to_config(row: tuple) -> dict:
    # service, feishu_webhook, feishu_enabled, smtp_host, smtp_port,
    # smtp_username, smtp_password, smtp_to_addrs, smtp_enabled, updated_at
    return {
        "service":          row[0],
        "display_name":     _SERVICE_LABELS.get(row[0], row[0]),
        "feishu_webhook":   row[1],
        "feishu_enabled":   bool(row[2]),
        "smtp_host":        row[3],
        "smtp_port":        row[4],
        "smtp_username":    row[5],
        "smtp_password_set": bool(row[6]),  # 不返回明文密码
        "smtp_to_addrs":    row[7],
        "smtp_enabled":     bool(row[8]),
        "updated_at":       row[9],
    }


@app.get("/api/v1/notifications/configs")
async def list_notification_configs(current_user: dict = Depends(get_current_user)):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT service,feishu_webhook,feishu_enabled,smtp_host,smtp_port,"
        "smtp_username,smtp_password,smtp_to_addrs,smtp_enabled,updated_at "
        "FROM notification_configs ORDER BY service"
    )
    rows = cursor.fetchall()
    conn.close()
    return [_row_to_config(r) for r in rows]


@app.put("/api/v1/notifications/configs/{service}")
async def update_notification_config(
    service: str,
    req: NotificationConfigRequest,
    admin: dict = Depends(require_admin),
):
    if service not in _SERVICE_LABELS:
        raise HTTPException(status_code=400, detail=f"未知服务: {service}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # 若密码为空则保留原密码
    if req.smtp_password:
        cursor.execute(
            "UPDATE notification_configs SET feishu_webhook=?,feishu_enabled=?,"
            "smtp_host=?,smtp_port=?,smtp_username=?,smtp_password=?,smtp_to_addrs=?,"
            "smtp_enabled=?,updated_at=? WHERE service=?",
            (req.feishu_webhook, 1 if req.feishu_enabled else 0,
             req.smtp_host, req.smtp_port, req.smtp_username, req.smtp_password,
             req.smtp_to_addrs, 1 if req.smtp_enabled else 0,
             datetime.now().isoformat(), service)
        )
    else:
        cursor.execute(
            "UPDATE notification_configs SET feishu_webhook=?,feishu_enabled=?,"
            "smtp_host=?,smtp_port=?,smtp_username=?,smtp_to_addrs=?,"
            "smtp_enabled=?,updated_at=? WHERE service=?",
            (req.feishu_webhook, 1 if req.feishu_enabled else 0,
             req.smtp_host, req.smtp_port, req.smtp_username,
             req.smtp_to_addrs, 1 if req.smtp_enabled else 0,
             datetime.now().isoformat(), service)
        )
    conn.commit()
    conn.close()
    return {"success": True}


@app.post("/api/v1/notifications/configs/{service}/test-feishu")
async def test_feishu(service: str, admin: dict = Depends(require_admin)):
    if service not in _SERVICE_LABELS:
        raise HTTPException(status_code=400, detail=f"未知服务: {service}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT feishu_webhook FROM notification_configs WHERE service=?", (service,))
    row = cursor.fetchone()
    conn.close()
    webhook = (row[0] if row else "").strip()
    if not webhook or not webhook.startswith("http"):
        raise HTTPException(status_code=400, detail="Feishu Webhook 未配置")

    import urllib.request as urlreq
    payload = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {"tag": "plain_text", "content": "📣 [DEV-NOTIFY] 测试通知"},
                "template": "turquoise",
            },
            "elements": [
                {"tag": "div", "text": {"tag": "lark_md", "content":
                    f"来自 **JBT Dashboard** 的测试通知\n服务：{_SERVICE_LABELS[service]}"}},
                {"tag": "note", "elements": [
                    {"tag": "plain_text", "content": f"JBT Dashboard | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"}
                ]},
            ],
        },
    }
    data = json.dumps(payload).encode()
    req_obj = urlreq.Request(webhook, data=data, headers={"Content-Type": "application/json"})
    try:
        with urlreq.urlopen(req_obj, timeout=10) as resp:
            result = json.loads(resp.read())
            ok = result.get("StatusCode", result.get("code", -1)) == 0
            return {"success": ok, "result": result}
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Feishu 请求失败: {e}")


@app.get("/api/v1/notifications/rules")
async def list_notification_rules(
    service: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    if service:
        cursor.execute(
            "SELECT id,service,name,rule_type,color,content_template,enabled,feishu_enabled,smtp_enabled,sort_order,created_at "
            "FROM notification_rules WHERE service=? ORDER BY sort_order,id",
            (service,)
        )
    else:
        cursor.execute(
            "SELECT id,service,name,rule_type,color,content_template,enabled,feishu_enabled,smtp_enabled,sort_order,created_at "
            "FROM notification_rules ORDER BY service,sort_order,id"
        )
    rows = cursor.fetchall()
    conn.close()
    return [
        {"id": r[0], "service": r[1], "name": r[2], "rule_type": r[3],
         "color": r[4], "content_template": r[5], "enabled": bool(r[6]),
         "feishu_enabled": bool(r[7]), "smtp_enabled": bool(r[8]),
         "sort_order": r[9], "created_at": r[10]}
        for r in rows
    ]


@app.post("/api/v1/notifications/rules", status_code=201)
async def create_notification_rule(
    req: NotificationRuleRequest,
    admin: dict = Depends(require_admin),
):
    valid_types = {"alarm_p0","alarm_p1","alarm_p2","trade","info","news","notify"}
    valid_colors = {"red","orange","yellow","grey","blue","wathet","turquoise"}
    if req.rule_type not in valid_types:
        raise HTTPException(status_code=400, detail=f"rule_type 必须为: {', '.join(valid_types)}")
    if req.color not in valid_colors:
        raise HTTPException(status_code=400, detail=f"color 必须为: {', '.join(valid_colors)}")
    now = datetime.now().isoformat()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO notification_rules (service,name,rule_type,color,content_template,enabled,feishu_enabled,smtp_enabled,sort_order,created_at,updated_at) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (req.service, req.name, req.rule_type, req.color, req.content_template,
         1 if req.enabled else 0, 1 if req.feishu_enabled else 0, 1 if req.smtp_enabled else 0,
         99, now, now)
    )
    rule_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return {"id": rule_id, "success": True}


@app.put("/api/v1/notifications/rules/{rule_id}")
async def update_notification_rule(
    rule_id: int,
    req: NotificationRuleRequest,
    admin: dict = Depends(require_admin),
):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM notification_rules WHERE id=?", (rule_id,))
    if cursor.fetchone()[0] == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="规则不存在")
    cursor.execute(
        "UPDATE notification_rules SET name=?,rule_type=?,color=?,content_template=?,enabled=?,feishu_enabled=?,smtp_enabled=?,updated_at=? WHERE id=?",
        (req.name, req.rule_type, req.color, req.content_template,
         1 if req.enabled else 0, 1 if req.feishu_enabled else 0, 1 if req.smtp_enabled else 0,
         datetime.now().isoformat(), rule_id)
    )
    conn.commit()
    conn.close()
    return {"success": True}


@app.delete("/api/v1/notifications/rules/{rule_id}")
async def delete_notification_rule(
    rule_id: int,
    admin: dict = Depends(require_admin),
):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM notification_rules WHERE id=?", (rule_id,))
    conn.commit()
    conn.close()
    return {"success": True}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3006)
