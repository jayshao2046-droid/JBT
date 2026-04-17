# Windows 任务计划配置脚本 - Alienware 研究员 24x7 自动化
#
# 功能：
# 1. 创建 Windows 任务计划，每小时触发研究员分析
# 2. 配置任务在系统启动时自动运行研究员服务
# 3. 配置日志轮转和错误恢复
#
# 使用方法：
# 1. 以管理员身份运行 PowerShell
# 2. 执行：.\setup_researcher_windows_task.ps1
#
# 部署位置：Alienware (192.168.31.223)

# 配置参数
$TaskName = "JBT_Researcher_Service"
$TaskNameHourly = "JBT_Researcher_Hourly"
$PythonExe = "C:\Users\17621\jbt\.venv\Scripts\python.exe"
$ServerScript = "C:\Users\17621\jbt\services\data\run_researcher_server.py"
$TriggerScript = "C:\Users\17621\jbt\services\data\scripts\trigger_researcher.py"
$WorkingDir = "C:\Users\17621\jbt"

Write-Host "=" * 60
Write-Host "JBT 研究员服务 - Windows 任务计划配置"
Write-Host "=" * 60

# 检查 Python 和脚本是否存在
if (-not (Test-Path $PythonExe)) {
    Write-Error "Python 可执行文件不存在: $PythonExe"
    exit 1
}

if (-not (Test-Path $ServerScript)) {
    Write-Error "服务脚本不存在: $ServerScript"
    exit 1
}

Write-Host "[1/4] 检查现有任务..."

# 删除已存在的任务
if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    Write-Host "删除现有服务任务: $TaskName"
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

if (Get-ScheduledTask -TaskName $TaskNameHourly -ErrorAction SilentlyContinue) {
    Write-Host "删除现有定时任务: $TaskNameHourly"
    Unregister-ScheduledTask -TaskName $TaskNameHourly -Confirm:$false
}

Write-Host "[2/4] 创建研究员服务任务（系统启动时运行）..."

# 创建服务任务（系统启动时运行）
$Action = New-ScheduledTaskAction -Execute $PythonExe -Argument $ServerScript -WorkingDirectory $WorkingDir
$Trigger = New-ScheduledTaskTrigger -AtStartup
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 5)
$Principal = New-ScheduledTaskPrincipal -UserId "17621" -LogonType Interactive -RunLevel Highest

Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Principal $Principal -Description "JBT 研究员服务 - 24x7 运行"

Write-Host "✓ 服务任务创建成功: $TaskName"

Write-Host "[3/4] 创建每小时触发任务..."

# 创建 24 个每小时触发任务（00:00 - 23:00）
for ($hour = 0; $hour -lt 24; $hour++) {
    $TaskNameHour = "${TaskNameHourly}_${hour}"

    # 删除已存在的任务
    if (Get-ScheduledTask -TaskName $TaskNameHour -ErrorAction SilentlyContinue) {
        Unregister-ScheduledTask -TaskName $TaskNameHour -Confirm:$false
    }

    # 创建触发器（每天指定小时的 00 分）
    $TriggerHour = New-ScheduledTaskTrigger -Daily -At ([DateTime]::Today.AddHours($hour))

    # 创建动作（调用触发脚本）
    $ActionHour = New-ScheduledTaskAction -Execute $PythonExe -Argument "$TriggerScript --hour $hour" -WorkingDirectory $WorkingDir

    # 注册任务
    Register-ScheduledTask -TaskName $TaskNameHour -Action $ActionHour -Trigger $TriggerHour -Settings $Settings -Principal $Principal -Description "JBT 研究员每小时触发 - ${hour}:00"

    Write-Host "  ✓ 创建任务: ${TaskNameHour} (${hour}:00)"
}

Write-Host "[4/4] 启动研究员服务..."

# 立即启动服务任务
Start-ScheduledTask -TaskName $TaskName

Write-Host ""
Write-Host "=" * 60
Write-Host "配置完成！"
Write-Host "=" * 60
Write-Host ""
Write-Host "已创建任务："
Write-Host "  1. $TaskName - 系统启动时自动运行服务"
Write-Host "  2. ${TaskNameHourly}_0 ~ ${TaskNameHourly}_23 - 每小时触发分析"
Write-Host ""
Write-Host "服务端口：8199"
Write-Host "日志位置：$WorkingDir\runtime\researcher\logs\server.log"
Write-Host ""
Write-Host "验证服务："
Write-Host "  curl http://localhost:8199/health"
Write-Host ""
Write-Host "手动触发："
Write-Host "  curl -X POST http://localhost:8199/run?hour=14"
Write-Host ""
