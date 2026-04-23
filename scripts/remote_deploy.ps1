# PowerShell 远程执行脚本
# 在 Alienware 上执行完整部署

$hostname = "192.168.31.187"
$username = "17621"
$scriptPath = "~/JBT/scripts/deploy_full_alienware.sh"

Write-Host "=========================================="
Write-Host "远程部署到 Alienware ($hostname)"
Write-Host "=========================================="
Write-Host ""

# 执行部署脚本
Write-Host "执行部署脚本..."
ssh "$username@$hostname" "bash $scriptPath"

Write-Host ""
Write-Host "=========================================="
Write-Host "部署完成！"
Write-Host "=========================================="
