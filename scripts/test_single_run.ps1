# 单次测试研究员完整流程

Write-Host "=== 触发研究员分析 ===" -ForegroundColor Green
curl.exe -X POST http://192.168.31.223:8199/trigger `
  -H "Content-Type: application/json" `
  -d '{\"force\": true}'

Write-Host "`n`n=== 等待30秒让分析完成 ===" -ForegroundColor Green
Start-Sleep -Seconds 30

Write-Host "`n=== 检查队列状态 ===" -ForegroundColor Green
curl.exe http://192.168.31.223:8199/queue/status

Write-Host "`n`n=== 检查 Studio decision 日志（最后20行）===" -ForegroundColor Green
ssh jaybot@192.168.31.142 "tail -20 /home/jaybot/jbt/services/decision/logs/app.log"

Write-Host "`n`n测试完成" -ForegroundColor Green
