# 仪表板登录问题排查与解决

**问题**: 登录页面显示 "用户名或密码错误"  
**日期**: 2026-04-21  
**状态**: ✅ 已解决

## 根本原因

1. **后端进程停止**：FastAPI 后端（3006）进程不在运行
2. **代码兼容性问题**：Python 3.9 不支持 `str | None` 类型注解语法（Python 3.10+才支持）

## 解决步骤

### 步骤 1：修复代码兼容性

**文件**: `services/dashboard/src/main.py` 第 1260 行

将 Python 3.10+ 语法改为 3.9 兼容：
```python
# ❌ 错误（Python 3.10+）
service: str | None = None

# ✅ 正确（Python 3.9）
service: Optional[str] = None
```

### 步骤 2：重启后端

```bash
cd /Users/jayshao/JBT/services/dashboard
source /Users/jayshao/JBT/.venv/bin/activate
python3 src/main.py
```

**预期输出**:
```
INFO:     Uvicorn running on http://0.0.0.0:3006 (Press CTRL+C to quit)
```

### 步骤 3：确保前端也在运行

```bash
cd /Users/jayshao/JBT/services/dashboard/dashboard_web
source /Users/jayshao/JBT/.venv/bin/activate
pnpm dev
```

## 验证

### 快速测试

```bash
# 1. 测试后端登录 API
curl -X POST http://localhost:3006/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"admin123"}'

# 2. 应该返回
{
  "success": true,
  "token": "...",
  "user": {...}
}

# 3. 前端访问
open http://localhost:3005
```

## 登录凭证

- **用户名**: `admin`
- **密码**: `admin123`

## 常见问题

### Q: 后端无法启动，报错 "port already in use"

```bash
# 查找占用 3006 的进程并杀死
lsof -i :3006 | grep LISTEN | awk '{print $2}' | xargs kill -9

# 重新启动
python3 src/main.py
```

### Q: 前端显示 "加载失败" 或 "网络错误"

1. 检查后端是否运行: `curl http://localhost:3006/health` （如果有此端点）
2. 检查 `.env.local` 是否配置了正确的后端 URL
3. 重启前端: `pnpm dev`

### Q: 登录成功但页面仍然卡在登录页

- 清除浏览器 localStorage: `localStorage.clear()` 在控制台
- 刷新页面并重新登录

## 相关文件

- 后端: `services/dashboard/src/main.py`
- 前端: `services/dashboard/dashboard_web/`
- 数据库: `services/dashboard/runtime/dashboard.db`

---

**维护者**: 看板 Agent  
**最后更新**: 2026-04-21
