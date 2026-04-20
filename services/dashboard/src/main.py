from __future__ import annotations

import hashlib
import hmac
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
    if path in _PUBLIC_PATHS or path.startswith("/api/v1/users") or path.startswith("/api/v1/auth"):
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

    # 创建默认管理员账户 admin/admin123
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
        """SELECT u.id, u.username, u.role, u.created_at
           FROM sessions s JOIN users u ON s.user_id = u.id
           WHERE s.token = ? AND s.expires_at > ?""",
        (token, datetime.now().isoformat()),
    )
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    return {"id": row[0], "username": row[1], "role": row[2], "created_at": row[3]}


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


class CreateUserRequest(BaseModel):
    username: str
    password: str
    role: str = "user"


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
    cursor.execute("SELECT id, username, role, created_at FROM users ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()

    return [User(id=r[0], username=r[1], role=r[2], created_at=r[3]) for r in rows]


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
    now = datetime.now().isoformat()

    cursor.execute(
        "INSERT INTO users (username, password_hash, role, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
        (req.username, password_hash, req.role, now, now)
    )
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return User(id=user_id, username=req.username, role=req.role, created_at=now)


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


@app.get("/health")
async def health():
    return {"status": "healthy", "service": SERVICE_NAME, "version": SERVICE_VERSION}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3006)
