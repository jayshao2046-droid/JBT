# Alienware 重启后任务交接

> **交接时间**: 2026-04-18  
> **执行端**: Alienware Windows VS Code 终端（PowerShell）  
> **工作区**: `C:\Users\17621\jbt`  
> **全部步骤按顺序执行，完成后截图给 MacBook 确认**

---

## 第一步：启动研究员服务（前台验证）

在 VS Code **终端 1** 中运行（保持前台，不要关闭）：

```powershell
cd C:\Users\17621\jbt
python -u -m services.data.run_researcher_server
```

等待看到以下输出后继续第二步：
```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8199
```

---

## 第二步：健康检查（新开终端 2）

```powershell
# 1. Researcher 服务
$r = Invoke-WebRequest -Uri "http://localhost:8199/health" -UseBasicParsing
Write-Output "=== Researcher 8199 ===" ; $r.StatusCode; $r.Content

# 2. 等待 3 分钟后检查日志是否持续写入
Start-Sleep -Seconds 180
$log = Get-Item "C:\Users\17621\jbt\runtime\researcher\logs\server.log"
Write-Output "=== 日志大小（应持续增长）===" ; $log.Length; $log.LastWriteTime

# 3. 检查今日文章数
$today = (Get-Date).ToString("yyyy-MM-dd")
$count = (Get-ChildItem "D:\researcher_reports\$today\articles\*.json" -ErrorAction SilentlyContinue).Count
Write-Output "=== 今日文章数 ===" ; $count

# 4. 检查各源文章分布（新增源是否有产出）
Get-ChildItem "D:\researcher_reports\$today\articles\*.json" -ErrorAction SilentlyContinue | ForEach-Object {
    (Get-Content $_.FullName -Raw | ConvertFrom-Json).source_id
} | Group-Object | Sort-Object Count -Descending | Format-Table Name,Count -AutoSize
```

**预期**：eastmoney_futures、kitco_gold、sci99、99futures 应开始出现

---

## 第三步：Sim-Trading 健康检查

```powershell
# Sim-Trading 在 Studio (192.168.31.142:8101)
try {
    $r = Invoke-WebRequest -Uri "http://192.168.31.142:8101/health" -UseBasicParsing -TimeoutSec 10
    Write-Output "=== Sim-Trading 8101 ===" ; $r.StatusCode; $r.Content
} catch {
    Write-Output "=== Sim-Trading 8101 FAIL ===" ; $_.Exception.Message
}

# Decision 服务
try {
    $r = Invoke-WebRequest -Uri "http://192.168.31.142:8104/health" -UseBasicParsing -TimeoutSec 10
    Write-Output "=== Decision 8104 ===" ; $r.StatusCode; $r.Content
} catch {
    Write-Output "=== Decision 8104 FAIL ===" ; $_.Exception.Message
}
```

---

## 第四步：注册 Windows 任务计划（看门狗 + 开机自启）

**必须以管理员身份运行 PowerShell**（右键 → 以管理员身份运行），然后执行：

```powershell
cd C:\Users\17621\jbt

# === 配置 ===
$TaskName   = "JBT_Researcher_Service"
$PythonExe  = "python"   # 使用系统 PATH 中的 python
$WorkingDir = "C:\Users\17621\jbt"
$LogFile    = "C:\Users\17621\jbt\runtime\researcher\logs\task_stdout.log"

# === 删除旧任务 ===
if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Output "已删除旧任务"
}

# === 创建启动动作 ===
$Action = New-ScheduledTaskAction `
    -Execute "cmd.exe" `
    -Argument "/c python -u -m services.data.run_researcher_server > C:\Users\17621\jbt\runtime\researcher\logs\task_stdout.log 2>&1" `
    -WorkingDirectory $WorkingDir

# === 触发器：开机时启动 ===
$Trigger = New-ScheduledTaskTrigger -AtStartup

# === 设置：崩溃后 2 分钟内重启，最多 3 次 ===
$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 2) `
    -ExecutionTimeLimit ([TimeSpan]::Zero)

# === 以当前用户最高权限运行 ===
$Principal = New-ScheduledTaskPrincipal `
    -UserId $env:USERNAME `
    -LogonType Interactive `
    -RunLevel Highest

# === 注册任务 ===
Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -Principal $Principal `
    -Description "JBT 研究员服务 24x7 - 开机自启，崩溃自恢复" `
    -Force

Write-Output "✅ 任务计划注册成功: $TaskName"

# === 验证 ===
Get-ScheduledTask -TaskName $TaskName | Select-Object TaskName,State | Format-Table -AutoSize
```

---

## 第五步：验证任务计划

```powershell
# 查看任务状态
Get-ScheduledTask -TaskName "JBT_Researcher_Service" | Format-List TaskName, State, Description

# 手动触发一次测试（确认能正常启动）
# 注意：此命令会启动一个新进程，如果 8199 已占用会报错，属正常
# Start-ScheduledTask -TaskName "JBT_Researcher_Service"
```

---

## 预期最终状态

| 检查项 | 预期结果 |
|--------|---------|
| `http://localhost:8199/health` | `{"status":"ok","service":"researcher"}` |
| 日志持续写入 | `server.log` 每 30~90s 增长 |
| 今日文章数 | > 旧值 231，且新源有产出 |
| 任务计划 | State = Ready |
| Sim-Trading 8101 | `{"status":"ok"}` |
| Decision 8104 | `{"status":"ok"}` |

---

## 如有问题

**Researcher 起不来**：在终端 1 查看完整错误输出，截图发给 MacBook

**任务计划注册失败**：确认是管理员 PowerShell，或改用 `SYSTEM` 账户：
```powershell
$Principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -RunLevel Highest
```

**8199 端口占用**（重启后理论上不会）：
```powershell
$pid = (netstat -ano | Select-String "8199.*LISTENING" | ForEach-Object { ($_ -split '\s+')[-1] })[0]
Stop-Process -Id $pid -Force
```

> **交接时间**: 2026-04-18 15:00
> **来源**: MacBook Atlas → Alienware 本地 VS Code
> **工作区**: `C:\Users\17621\jbt`
> **服务**: `services/data/run_researcher_server.py` (端口 8199)

---

## 当前状态

代码已全部更新到 Alienware 本地（5 个文件已 SFTP + MD5 校验通过），但服务需要重启验证。

## 已完成的代码修改（5 个文件）

### 1. `services/data/run_researcher_server.py` — 日志修复
- **移除** QueueHandler + QueueListener（Windows daemon 线程丢日志）
- **改为** 直接挂 FlushFileHandler + StreamHandler 到 root logger
- 每轮循环结束后显式 `_flush_all_logs()`
- 添加 `atexit.register(_flush_all_logs)` 确保退出时 flush

### 2. `services/data/configs/researcher_sources.yaml` — URL 修复
| 源 | 旧 URL | 新 URL | 原因 |
|----|--------|--------|------|
| eastmoney_futures | `futures.eastmoney.com/news/` | `futures.eastmoney.com/` | `/news/` 返回空页面 |
| mysteel | `mysteel.com/news/` (code) | `mysteel.com/` (browser) | 403 封锁，改 browser 模式 |
| sci99 | `sci99.com/news/` | `sci99.com/` | `/news/` 302→404 |
| 99futures | `99qh.com/news/` | `99qh.com/` | `/news/` 308→404 |
| kitco_gold | `kitco.com/news/precious-metals/` | `kitco.com/news` | 旧路径 404 |

### 3. `services/data/src/researcher/crawler/parsers/futures.py` — 解析器适配
- **eastmoney**: xpath 改为 `//a[contains(@href,'/a/')]`（首页新闻链接）
- **mysteel**: xpath 改为 `//a[contains(@href,'mysteel.com')]`
- **sci99**: xpath 改为 `//a[contains(@href,'sci99.com')]`
- **99futures**: xpath 改为 `//a[contains(@href,'99qh.com')]`

### 4. `services/data/src/researcher/crawler/parsers/international.py` — Kitco 修复
- **kitco_gold**: xpath 改为 `//a[contains(@href,'/news/article/')]`

### 5. `services/data/src/researcher/staging.py` — Symbol 格式修复
- 移除 `symbol.replace(".", "_").replace("@", "_")` 
- 直接传原始 symbol（如 `KQ.m@SHFE.rb`）给 Mini API

---

## 需要执行的操作

### 第一步：停止旧进程 + 清缓存
```powershell
Get-Process -Name python,chromium -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 5

# 清除所有 __pycache__
Remove-Item -Recurse -Force "C:\Users\17621\jbt\services\data\src\researcher\__pycache__" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "C:\Users\17621\jbt\services\data\src\researcher\crawler\__pycache__" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "C:\Users\17621\jbt\services\data\src\researcher\crawler\parsers\__pycache__" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "C:\Users\17621\jbt\services\data\__pycache__" -ErrorAction SilentlyContinue
```

### 第二步：前台启动服务
```powershell
cd C:\Users\17621\jbt
python -u -m services.data.run_researcher_server
```

**关键**：
- 必须用 `python -u`（unbuffered）前台运行
- **禁止** 使用 `-RedirectStandardError` 或 `-WindowStyle Hidden`（会导致 Playwright 崩溃）
- 终端会实时显示所有日志和错误

### 第三步：验证清单

在另一个终端中执行：

```powershell
# 1. 健康检查
curl http://localhost:8199/health

# 2. 等待 2-3 分钟，检查日志是否持续写入
Get-Item "C:\Users\17621\jbt\runtime\researcher\logs\server.log" | Select-Object Length,LastWriteTime

# 3. 检查新文章数
$today = (Get-Date).ToString("yyyy-MM-dd")
(Get-ChildItem "D:\researcher_reports\$today\articles\*.json" -ErrorAction SilentlyContinue).Count

# 4. 检查源覆盖（看哪些源产出了文章）
Get-ChildItem "D:\researcher_reports\$today\articles\*.json" | ForEach-Object {
    (Get-Content $_.FullName | ConvertFrom-Json).source_id
} | Group-Object | Sort-Object Count -Descending | Format-Table Name,Count
```

### 预期结果
- **健康检查**: `{"status":"ok","service":"researcher",...}`
- **日志**: 持续增长，不再冻结
- **新增源**: eastmoney_futures、kitco_gold、sci99、99futures 应开始产出文章
- **已有源**: jin10、oilprice、investing、sina、cffex、hexun 继续正常

---

## 已知遗留

1. **中文日志乱码**: `server.log` 中部分中文显示为 `�?`，原因是 Windows GBK/UTF-8 冲突。日志文件用 `encoding="utf-8"` 写入，用 UTF-8 编辑器打开应正常
2. **mysteel**: 即使改为 browser 模式，仍可能被反爬封锁（403）。如果持续失败，可在 YAML 中设 `enabled: false`
3. **Mini K-line**: Mini 无分钟线数据（symbols count=0），K-line 分析阶段会跳过但不报错

---

## 回滚方案

如果新版本有问题，旧版本备份在 git 历史中。在 MacBook 上：
```bash
cd ~/JBT
git stash  # 暂存当前修改
# 取出旧版本文件重新 SFTP 部署
```

---

## 附：重启前环境诊断清单

> **在 VS Code 终端中运行以下命令，把结果截图给 MacBook 端确认后再重启。**

### A. Python 环境

```powershell
cd C:\Users\17621\jbt
python --version
python -c "import sys; print(sys.executable)"
python -m pip list | Select-String "fastapi|uvicorn|httpx|playwright|lxml|pydantic|yaml|aiohttp|aiosqlite"
```

### B. Playwright 浏览器

```powershell
python -m playwright install --dry-run
python -c "from playwright.sync_api import sync_playwright; p = sync_playwright().start(); b = p.chromium.launch(); print('OK browser'); b.close(); p.stop()"
```

### C. 关键目录与文件

```powershell
# 报告目录
Test-Path "D:\researcher_reports" && (Get-ChildItem "D:\researcher_reports" -Recurse -File | Measure-Object).Count

# 日志目录
Test-Path "C:\Users\17621\jbt\runtime\researcher\logs"
Get-ChildItem "C:\Users\17621\jbt\runtime\researcher\logs"

# 5 个热修文件是否存在
@(
  "services\data\run_researcher_server.py",
  "services\data\configs\researcher_sources.yaml",
  "services\data\src\researcher\staging.py",
  "services\data\src\researcher\crawler\parsers\futures.py",
  "services\data\src\researcher\crawler\parsers\international.py"
) | ForEach-Object { [PSCustomObject]@{File=$_; Exists=Test-Path "C:\Users\17621\jbt\$_"} }
```

### D. 端口占用检查

```powershell
netstat -ano | Select-String "8199"
# 如果有输出，记录 PID（最右列）
# 重启后这些进程应消失
```

### E. 网络连通性

```powershell
# Mini data API
curl http://192.168.31.156:8105/api/v1/health -UseBasicParsing | Select-Object StatusCode

# Studio decision API
curl http://192.168.31.142:8104/api/v1/health -UseBasicParsing -ErrorAction SilentlyContinue | Select-Object StatusCode

# Ollama 本机
curl http://localhost:11434/api/version -UseBasicParsing | Select-Object StatusCode,Content
```

### F. 重启后启动命令（贴在桌面便签）

```powershell
cd C:\Users\17621\jbt
python -u -m services.data.run_researcher_server
```

**必须前台运行，禁止 -WindowStyle Hidden 或 -RedirectStandardError**
