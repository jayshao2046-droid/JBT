# Alienware 部署和测试脚本
# 在 Alienware (192.168.31.187) 上以管理员身份运行

Write-Host "=========================================="
Write-Host "JBT 研究员系统部署和测试"
Write-Host "时间: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Host "=========================================="
Write-Host ""

# 配置
$JBT_ROOT = "C:\Users\17621\jbt"
$DATA_SERVICE = "$JBT_ROOT\services\data"
$VENV_PYTHON = "$JBT_ROOT\.venv\Scripts\python.exe"

# 步骤 1：检查 Git 状态
Write-Host "[1/7] 检查代码版本..."
Write-Host ""

Set-Location $JBT_ROOT

$gitStatus = git status --short
if ($gitStatus) {
    Write-Host "  未提交的修改:"
    Write-Host $gitStatus
    Write-Host ""
    $continue = Read-Host "  是否继续部署? (y/n)"
    if ($continue -ne "y") {
        Write-Host "部署已取消"
        exit 1
    }
}

# 拉取最新代码
Write-Host "  拉取最新代码..."
git pull
Write-Host ""

# 步骤 2：检查 Python 环境
Write-Host "[2/7] 检查 Python 环境..."
Write-Host ""

if (-not (Test-Path $VENV_PYTHON)) {
    Write-Host "  错误: Python 虚拟环境不存在: $VENV_PYTHON"
    exit 1
}

$pythonVersion = & $VENV_PYTHON --version
Write-Host "  Python 版本: $pythonVersion"
Write-Host ""

# 步骤 3：检查依赖
Write-Host "[3/7] 检查依赖..."
Write-Host ""

$requiredModules = @("fastapi", "uvicorn", "httpx", "pydantic")
foreach ($module in $requiredModules) {
    $installed = & $VENV_PYTHON -c "import $module; print('OK')" 2>$null
    if ($installed -eq "OK") {
        Write-Host "  ✓ $module"
    } else {
        Write-Host "  ✗ $module (缺失)"
        Write-Host "    安装中..."
        & $VENV_PYTHON -m pip install $module
    }
}
Write-Host ""

# 步骤 4：创建必要目录
Write-Host "[4/7] 创建必要目录..."
Write-Host ""

$dirs = @(
    "$JBT_ROOT\runtime\researcher\logs",
    "D:\researcher_reports\.queue"
)

foreach ($dir in $dirs) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "  ✓ 创建: $dir"
    } else {
        Write-Host "  ✓ 已存在: $dir"
    }
}
Write-Host ""

# 步骤 5：配置 Windows 任务计划
Write-Host "[5/7] 配置 Windows 任务计划..."
Write-Host ""

$setupScript = "$DATA_SERVICE\scripts\setup_researcher_windows_task.ps1"
if (Test-Path $setupScript) {
    Write-Host "  执行任务计划配置脚本..."
    & $setupScript
} else {
    Write-Host "  警告: 任务计划配置脚本不存在: $setupScript"
    Write-Host "  跳过任务计划配置"
}
Write-Host ""

# 步骤 6：启动研究员服务
Write-Host "[6/7] 启动研究员服务..."
Write-Host ""

# 检查服务是否已运行
$existingProcess = Get-Process -Name python -ErrorAction SilentlyContinue | Where-Object {
    $_.CommandLine -like "*run_researcher_server.py*"
}

if ($existingProcess) {
    Write-Host "  服务已在运行 (PID: $($existingProcess.Id))"
    $restart = Read-Host "  是否重启服务? (y/n)"
    if ($restart -eq "y") {
        Write-Host "  停止现有服务..."
        Stop-Process -Id $existingProcess.Id -Force
        Start-Sleep -Seconds 2
    } else {
        Write-Host "  保持现有服务运行"
        Write-Host ""
        Write-Host "跳到步骤 7 进行测试..."
        Write-Host ""
        goto :test
    }
}

# 启动服务
Write-Host "  启动研究员服务..."
Set-Location $DATA_SERVICE

$logFile = "$JBT_ROOT\runtime\researcher\logs\server.log"
Start-Process -FilePath $VENV_PYTHON -ArgumentList "run_researcher_server.py" -NoNewWindow -RedirectStandardOutput $logFile -RedirectStandardError $logFile

Write-Host "  等待服务启动 (5秒)..."
Start-Sleep -Seconds 5
Write-Host ""

# 步骤 7：测试服务
:test
Write-Host "[7/7] 测试服务..."
Write-Host ""

# 测试健康检查
Write-Host "  测试 1: 健康检查..."
try {
    $health = Invoke-RestMethod -Uri "http://localhost:8199/health" -Method Get
    Write-Host "  ✓ 服务正常运行"
    Write-Host "    状态: $($health.status)"
    Write-Host "    模型: $($health.model)"
} catch {
    Write-Host "  ✗ 服务不可用"
    Write-Host "    错误: $_"
    Write-Host ""
    Write-Host "查看日志:"
    Write-Host "  Get-Content $logFile -Tail 20"
    exit 1
}
Write-Host ""

# 测试队列状态
Write-Host "  测试 2: 队列状态..."
try {
    $queue = Invoke-RestMethod -Uri "http://localhost:8199/queue/status" -Method Get
    Write-Host "  ✓ 队列查询成功"
    Write-Host "    待读: $($queue.pending_count)"
    Write-Host "    处理中: $($queue.processing_count)"
} catch {
    Write-Host "  ✗ 队列查询失败"
    Write-Host "    错误: $_"
}
Write-Host ""

# 测试手动触发
Write-Host "  测试 3: 手动触发研究员..."
$currentHour = (Get-Date).Hour
Write-Host "    当前小时: $currentHour"

try {
    $trigger = Invoke-RestMethod -Uri "http://localhost:8199/run?hour=$currentHour" -Method Post
    Write-Host "  ✓ 触发成功"
    Write-Host "    批次: $($trigger.batch_id)"
} catch {
    Write-Host "  ✗ 触发失败"
    Write-Host "    错误: $_"
}
Write-Host ""

# 等待研究员执行
Write-Host "  等待研究员执行 (30秒)..."
Start-Sleep -Seconds 30
Write-Host ""

# 再次检查队列状态
Write-Host "  测试 4: 验证报告生成..."
try {
    $queueAfter = Invoke-RestMethod -Uri "http://localhost:8199/queue/status" -Method Get
    Write-Host "  ✓ 队列状态更新"
    Write-Host "    待读: $($queue.pending_count) → $($queueAfter.pending_count)"

    if ($queueAfter.pending_count -gt $queue.pending_count) {
        Write-Host "  ✓ 新报告已生成"
    } else {
        Write-Host "  ⚠ 未检测到新报告（可能数据不足或执行失败）"
    }
} catch {
    Write-Host "  ✗ 队列查询失败"
}
Write-Host ""

# 完成
Write-Host "=========================================="
Write-Host "部署和测试完成"
Write-Host "=========================================="
Write-Host ""
Write-Host "服务状态:"
Write-Host "  端口: 8199"
Write-Host "  日志: $logFile"
Write-Host "  队列: D:\researcher_reports\.queue\"
Write-Host ""
Write-Host "查看日志:"
Write-Host "  Get-Content $logFile -Tail 50 -Wait"
Write-Host ""
Write-Host "查看队列:"
Write-Host "  Get-Content D:\researcher_reports\.queue\pending.jsonl"
Write-Host ""
Write-Host "手动触发:"
Write-Host "  Invoke-RestMethod -Uri 'http://localhost:8199/run?hour=14' -Method Post"
Write-Host ""
