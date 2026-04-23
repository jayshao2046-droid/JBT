#!/bin/bash
# 单次测试研究员完整流程

echo "=== 触发研究员分析 ==="
curl -X POST http://192.168.31.187:8199/trigger \
  -H "Content-Type: application/json" \
  -d '{"force": true}'

echo -e "\n\n=== 等待30秒让分析完成 ==="
sleep 30

echo -e "\n=== 检查队列状态 ==="
curl http://192.168.31.187:8199/queue/status

echo -e "\n\n=== 检查 Studio decision 日志（最后20行）==="
ssh jaybot@192.168.31.142 "tail -20 /home/jaybot/JBT/services/decision/logs/app.log"

echo -e "\n\n测试完成"
