# Alienware 部署和测试指南

## 快速开始

在 Alienware (192.168.31.223) 上以**管理员身份**打开 PowerShell，执行：

```powershell
cd C:\Users\17621\jbt\scripts
.\deploy_alienware.ps1
```

这个脚本会自动完成：
1. 拉取最新代码
2. 检查 Python 环境和依赖
3. 创建必要目录
4. 配置 Windows 任务计划（25个任务）
5. 启动研究员服务（端口 8199）
6. 运行测试验证

## 手动部署步骤

如果自动脚本失败，可以手动执行以下步骤：

### 1. 拉取代码

```powershell
cd C:\Users\17621\jbt
git pull
```

### 2. 创建目录

```powershell
New-Item -ItemType Directory -Path "C:\Users\17621\jbt\runtime\researcher\logs" -Force
New-Item -ItemType Directory -Path "D:\researcher_reports\.queue" -Force
```

### 3. 配置任务计划

```powershell
cd C:\Users\17621\jbt\services\data\scripts
.\setup_researcher_windows_task.ps1
```

### 4. 启动服务

```powershell
cd C:\Users\17621\jbt\services\data
C:\Users\17621\jbt\.venv\Scripts\python.exe run_researcher_server.py
```

### 5. 验证服务

在另一个 PowerShell 窗口：

```powershell
# 健康检查
Invoke-RestMethod -Uri "http://localhost:8199/health" -Method Get

# 队列状态
Invoke-RestMethod -Uri "http://localhost:8199/queue/status" -Method Get

# 手动触发
Invoke-RestMethod -Uri "http://localhost:8199/run?hour=14" -Method Post
```

## 测试完整流程

### 1. 触发研究员分析

```powershell
$hour = (Get-Date).Hour
Invoke-RestMethod -Uri "http://localhost:8199/run?hour=$hour" -Method Post
```

### 2. 查看日志

```powershell
# 实时查看服务日志
Get-Content C:\Users\17621\jbt\runtime\researcher\logs\server.log -Tail 50 -Wait

# 查看关键日志
Get-Content C:\Users\17621\jbt\runtime\researcher\logs\server.log | Select-String -Pattern "QUEUE|REPORT_SAVE|API"
```

### 3. 检查队列

```powershell
# 查看待读队列
Get-Content D:\researcher_reports\.queue\pending.jsonl

# 查看已完成队列
Get-Content D:\researcher_reports\.queue\completed.jsonl
```

### 4. 检查报告文件

```powershell
# 查看今日报告
$today = Get-Date -Format "yyyy-MM-dd"
Get-ChildItem "D:\researcher_reports\$today"
```

## 验证 Studio 集成

### 1. 在 MacBook Air 上重启 Studio 服务

```bash
ssh jay@192.168.31.142 'bash -s' < /Users/jayshao/JBT/scripts/restart_studio_decision.sh
```

### 2. 验证 Studio 服务

```bash
curl http://192.168.31.142:8104/health
```

### 3. 触发完整流程测试

```bash
# 在 MacBook Air 上
cd /Users/jayshao/JBT
./scripts/test_researcher_flow.sh
```

## 常见问题

### Q1: 服务启动失败

**检查**：
```powershell
# 查看错误日志
Get-Content C:\Users\17621\jbt\runtime\researcher\logs\server.log -Tail 20
```

**可能原因**：
- Python 依赖缺失：运行 `pip install -r requirements.txt`
- 端口被占用：检查 8199 端口
- 权限不足：以管理员身份运行

### Q2: 队列为空

**检查**：
```powershell
# 查看报告目录
Get-ChildItem D:\researcher_reports -Recurse

# 手动触发
Invoke-RestMethod -Uri "http://localhost:8199/run?hour=14" -Method Post
```

### Q3: Studio 无法读取报告

**检查**：
```bash
# 测试网络连通性
curl http://192.168.31.223:8199/health

# 测试报告读取
curl http://192.168.31.223:8199/reports/latest
```

## 日志位置

- **服务日志**：`C:\Users\17621\jbt\runtime\researcher\logs\server.log`
- **队列文件**：`D:\researcher_reports\.queue\*.jsonl`
- **报告文件**：`D:\researcher_reports\{date}\*.json`

## 关键日志关键词

- `[QUEUE]` - 队列操作
- `[REPORT_SAVE]` - 报告保存
- `[API]` - API 调用
- `[PUSH]` - 推送到 Studio
- `[TRIGGER]` - 手动触发

## 下一步

部署完成后，等待下午开盘（13:30）观察自动运行情况，或手动触发测试完整流程。
