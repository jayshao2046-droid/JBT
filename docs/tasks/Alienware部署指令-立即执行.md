# Alienware 部署指令 - 立即执行

**时间**: 2026-04-17 17:15  
**目标**: 部署最新研究员服务代码到 Alienware  
**原因**: 当前运行的是旧版本，缺少队列管理 API

---

## 问题诊断

当前 Alienware 服务器返回的 `/queue/status` 端点输出：
```json
{
  "endpoints": [
    "GET  /status",
    "GET  /reports/latest",
    ...
  ]
}
```

这是旧版本的端点列表，而非实际队列状态。最新代码应返回：
```json
{
  "pending_count": 0,
  "processing_count": 0,
  "pending_reports": [],
  "timestamp": "2026-04-17T17:15:00"
}
```

---

## 部署步骤

### 1. 在 Alienware 上打开 PowerShell（管理员权限）

### 2. 停止现有服务

```powershell
# 查找并停止 Python 进程
Get-Process | Where-Object {$_.ProcessName -like '*python*'} | Stop-Process -Force

# 确认已停止
Get-Process | Where-Object {$_.ProcessName -like '*python*'}
```

### 3. 拉取最新代码

```powershell
cd C:\Users\17621\jbt

# 拉取最新代码
git pull origin main

# 查看最新提交
git log -1 --oneline
# 应该看到: 4eba220 feat: 研究员24x7自动化与数据流完善
```

### 4. 启动服务

```powershell
cd C:\Users\17621\jbt

# 启动研究员服务
python services\data\run_researcher_server.py

# 或者使用后台启动（推荐）
Start-Process python -ArgumentList "services\data\run_researcher_server.py" -WindowStyle Hidden
```

### 5. 验证服务

在另一个 PowerShell 窗口执行：

```powershell
# 测试健康检查
Invoke-WebRequest -Uri "http://localhost:8199/health" -UseBasicParsing

# 测试队列状态（应该返回 JSON 格式的队列信息）
Invoke-WebRequest -Uri "http://localhost:8199/queue/status" -UseBasicParsing | Select-Object -ExpandProperty Content
```

**预期输出**：
```json
{
  "pending_count": 0,
  "processing_count": 0,
  "pending_reports": [],
  "timestamp": "2026-04-17T17:15:00"
}
```

### 6. 触发测试

```powershell
# 触发研究员分析
$body = @{hour=17} | ConvertTo-Json
Invoke-WebRequest -Uri "http://localhost:8199/run" -Method POST -Body $body -ContentType "application/json" -UseBasicParsing

# 等待 30 秒
Start-Sleep -Seconds 30

# 再次检查队列状态
Invoke-WebRequest -Uri "http://localhost:8199/queue/status" -UseBasicParsing | Select-Object -ExpandProperty Content
```

---

## 常见问题

### Q1: git pull 失败，提示 "not a git repository"

**解决**：
```powershell
cd C:\Users\17621\jbt
git init
git remote add origin https://github.com/jayshao2046-droid/JBT.git
git fetch origin
git reset --hard origin/main
```

### Q2: Python 找不到模块

**解决**：
```powershell
# 确认 Python 环境
python --version

# 安装依赖
pip install -r requirements.txt
```

### Q3: 端口 8199 被占用

**解决**：
```powershell
# 查找占用端口的进程
netstat -ano | findstr :8199

# 停止进程（替换 <PID> 为实际进程 ID）
taskkill /PID <PID> /F
```

---

## 部署完成后

在 MacBook Air 上执行测试脚本：
```bash
python3 /Users/jayshao/JBT/scripts/test_researcher_python.py
```

应该看到：
- ✓ 队列状态正常返回
- ✓ 报告生成并入队
- ✓ 标记已读成功

---

## 联系信息

如有问题，检查日志：
```powershell
Get-Content C:\Users\17621\jbt\runtime\researcher\logs\server.log -Tail 50
```
