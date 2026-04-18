# JBT Researcher hourly task installer - Alienware
# Usage: powershell -ExecutionPolicy Bypass -File install_hourly_tasks.ps1

$PythonExe = "C:\Users\17621\AppData\Local\Programs\Python\Python311\python.exe"
$TriggerScript = "C:\Users\17621\jbt\services\data\scripts\trigger_researcher.py"
$WorkingDir = "C:\Users\17621\jbt"
$TaskNameHourly = "JBT_Researcher_Hourly"

Write-Output "=== JBT Researcher 24h Task Installer ==="

$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 10)

$Principal = New-ScheduledTaskPrincipal -UserId "17621" -LogonType Interactive -RunLevel Highest

$created = 0
for ($hour = 0; $hour -lt 24; $hour++) {
    $TaskNameHour = "${TaskNameHourly}_${hour}"
    Unregister-ScheduledTask -TaskName $TaskNameHour -Confirm:$false -ErrorAction SilentlyContinue
    $TriggerHour = New-ScheduledTaskTrigger -Daily -At ([DateTime]::Today.AddHours($hour))
    $ActionHour = New-ScheduledTaskAction -Execute $PythonExe -Argument "$TriggerScript --hour $hour" -WorkingDirectory $WorkingDir
    Register-ScheduledTask -TaskName $TaskNameHour -Action $ActionHour -Trigger $TriggerHour -Settings $Settings -Principal $Principal -Description "JBT Researcher trigger ${hour}:00" -Force | Out-Null
    $created++
}

Write-Output "Created $created hourly tasks"
Write-Output ""
Write-Output "Registered JBT tasks:"
Get-ScheduledTask | Where-Object { $_.TaskName -like "JBT_Researcher*" } | Select-Object TaskName, State | Format-Table -AutoSize
