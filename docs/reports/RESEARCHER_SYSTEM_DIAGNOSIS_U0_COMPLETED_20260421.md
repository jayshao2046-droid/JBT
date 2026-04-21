# U0 诊断完成总结 — 研究员系统故障 

【日期】2026-04-21 16:15  
【模式】U0 架构纠正与故障定位  
【状态】🔴 关键故障已定位  

---

## 真实架构确认

✅ **Alienware 直连 Decision**（已验证）
- Decision `ResearcherLoader` 配置：`http://192.168.31.223:8199`
- 端点：`GET /reports/latest`
- Mini 研报 API 是**可选备用**，不是关键路径
- P0"实现 Mini API"的需求**已作废**

---

## 关键故障发现

### 🔴 故障 1：Alienware 研报生成已停止 5 天

**症状**：
- 最新报告：2026-04-16 16:00（距今 5+ 天）
- 最新报告为空（无采集数据）
- curl 调用 `/reports/latest` 返回 404 + 正确的文件缺失提示

**根本原因**：
- Alienware 调度器最后执行时间：**2026-04-17 20:54**
- 日志最后记录：推送到 Decision 的端点返回 **404 Not Found**
- **结论**：研究员调度进程在 04-17 20:54 后就停止运行了

### 🔴 故障 2：Alienware 调度进程未重启

**症状**：
- 虽然 HTTP API 8199 还在响应（`/health` 返回 ok）
- 但**报告生成进程（scheduler）已停止**

**根本原因**：
- 可能原因 1：Decision 端的推送端点改变（返回 404）导致进程异常退出
- 可能原因 2：调度进程崩溃，未被自动重启
- 需要进一步检查启动脚本或 Windows 任务计划

---

## 验证清单

| 检查项 | 结果 | 状态 |
|------|------|------|
| Alienware 8199 HTTP 服务 | ✅ 正在运行（时间戳 13:46:28） | 工作中 |
| Alienware `/reports/latest` 端点 | ✅ 端点存在 | 工作中 |
| Alienware 报告存储 | ✅ D 盘存储完整 | 工作中 |
| **Alienware 报告生成进程** | ❌ 自 04-17 20:54 停止 | **故障** |
| Mini 采集管道 | ✅ news_api 每分钟采集 111 条 | 工作中 |
| Mini scheduler | ✅ 39 个任务已注册 | 工作中 |
| Decision ResearcherLoader | ✅ 代码配置正确 | 工作中 |
| **报告数据可用性** | ❌ 无新报告（5+ 天停滞） | **故障** |

---

## 紧急行动项（优先级排序）

### Priority 1 - 重启 Alienware 研究员进程（立即执行）

```bash
# Alienware 上检查进程
ssh 17621@192.168.31.223 'tasklist | findstr python'

# 如果研究员进程不存在，需要重启
ssh 17621@192.168.31.223 'C:\Users\17621\jbt\services\data\start_researcher.bat'

# 验证重启后是否有新报告生成
sleep 5
ssh 17621@192.168.31.223 'powershell -Command "Get-ChildItem C:\Users\17621\jbt\services\data\runtime\researcher\reports\2026-04-21\ -Filter *.json | Sort-Object LastWriteTime | Select-Object -Last 3"'
```

### Priority 2 - 调查 04-17 20:54 的故障原因

- Decision 端的 `/api/v1/researcher/evaluate` 端点为什么返回 404？
- 是否 Decision 的 API 路由改变了？
- 检查 Decision 日志中是否有相关记录

### Priority 3 - 建立监控告警

- 建立 watchdog 检查 Alienware scheduler 进程
- 如果进程不存在，自动重启
- 配置告警当报告生成停滞超过 2 小时

---

## 使用者确认项

**待 Jay.S 确认**：
1. ✅ 架构理解已纠正：Alienware 直连 Decision，无需 Mini API 中转
2. ❌ Alienware 研究员进程已停止 5 天 —— **需要立即重启**
3. ⚠️ 调查 04-17 20:54 推送失败的原因

---

**下一步**：
1. 重启 Alienware 研究员服务
2. 验证是否恢复生成新报告
3. 如果恢复，确认 Decision 端是否开始消费新报告
4. 建立持久化的进程监控

**未来优化**：
- Decision 不应该只依赖 Alienware 单点
- 考虑将最新报告缓存到 Mini（目前已支持，但未被使用）
- 建立更完善的故障转移机制
