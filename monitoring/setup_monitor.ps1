# Alienware 进程监控 watchdog — 每 5 分钟被任务计划程序调起（或也可单独常驻）
# 实际部署方式：
#   方式 A (推荐) — 直接注册为每 5 分钟的 Windows Scheduled Task，每次运行采样一次后退出
#   方式 B — 以常驻进程运行，内含自己的 sleep 循环（当前实现）
#
# 注册方式 A（推荐，更健壮）:
#   $action = New-ScheduledTaskAction -Execute "python" -Argument "C:\Users\17621\jbt\monitoring\alienware_monitor.py --once" -WorkingDirectory "C:\Users\17621\jbt"
#   $trigger = New-ScheduledTaskTrigger -RepetitionInterval (New-TimeSpan -Minutes 5) -Once -At "00:00"
#   Register-ScheduledTask -Action $action -Trigger $trigger -TaskName "JBT_ProcessMonitor" -RunLevel Highest -Force

param(
    [switch]$Install,
    [switch]$Uninstall,
    [switch]$Status
)

$TaskName   = "JBT_ProcessMonitor"
$ScriptPath = "C:\Users\17621\jbt\monitoring\alienware_monitor.py"
$WorkDir    = "C:\Users\17621\jbt"
$LogPath    = "C:\Users\17621\jbt\monitoring\watchdog.log"

function Write-Log {
    param([string]$Msg)
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$ts [JBT_Monitor] $Msg" | Tee-Object -Append -FilePath $LogPath
}

if ($Uninstall) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
    Write-Log "已卸载定时任务 $TaskName"
    exit 0
}

if ($Status) {
    $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($task) {
        Write-Host "任务状态: $($task.State)"
        Get-ScheduledTaskInfo -TaskName $TaskName | Select-Object LastRunTime,NextRunTime,LastTaskResult
    } else {
        Write-Host "未注册"
    }
    exit 0
}

if ($Install) {
    # 找 python 路径
    $PythonExe = (Get-Command python -ErrorAction SilentlyContinue).Source
    if (-not $PythonExe) {
        $PythonExe = "C:\Users\17621\AppData\Local\Programs\Python\Python312\python.exe"
    }

    # 每 5 分钟触发一次（--once 模式，采样后退出，由任务计划程序周期触发）
    $action  = New-ScheduledTaskAction `
        -Execute $PythonExe `
        -Argument "$ScriptPath --once" `
        -WorkingDirectory $WorkDir

    # RepetitionInterval 需要先创建 Once trigger，再加 repetition
    $startTime = (Get-Date).AddMinutes(1).ToString("yyyy-MM-ddTHH:mm:ss")
    $trigger = New-ScheduledTaskTrigger -Once -At $startTime `
        -RepetitionInterval (New-TimeSpan -Minutes 5) `
        -RepetitionDuration ([System.TimeSpan]::MaxValue)

    $settings = New-ScheduledTaskSettingsSet `
        -ExecutionTimeLimit (New-TimeSpan -Minutes 4) `
        -MultipleInstances IgnoreNew `
        -StartWhenAvailable

    $principal = New-ScheduledTaskPrincipal `
        -UserId "$env:USERNAME" `
        -RunLevel Highest `
        -LogonType Interactive

    Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -Principal $principal `
        -Force | Out-Null

    Write-Log "已注册定时任务 $TaskName (每5分钟, RunLevel Highest)"
    Write-Host "注册成功: $TaskName"
    exit 0
}

Write-Host "用法: .\setup_monitor.ps1 -Install | -Uninstall | -Status"
