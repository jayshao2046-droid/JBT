# TASK-0125 Mini数据回补验证与完整流程收口

【类型】标准任务  
【建档】Atlas  
【日期】2026-04-17  
【状态】待执行（预计 2026-04-19 或夜盘验证通过后）  
【优先级】P1  
【前置任务】TASK-U0-20260417-005（已收口）  
【Token】暂不签发，执行前再建审批

---

## 1. 背景

TASK-U0-20260417-005 已完成 Mini 数据保存故障四项根因修复：
- `pipeline.py` 写模式 `w→a`
- `Dockerfile` 时区 UTC→CST
- `docker-compose.dev.yml` volume→bind mount
- `queue/` → `task_queue/`（模块冲突）

遗留问题：
- 4月9-17日分钟K线数据缺口（TqSdk 回测模式限制，需实时采集填补）
- 完整数据流（Mini→Alienware→Studio→飞书）未经端到端验证

---

## 2. 待验证事项

### 2.1 夜盘实时采集验证（2026-04-17 21:00 后）

```bash
# 等待夜盘开始后执行
ssh jaybot@192.168.31.76 "docker exec JBT-DATA-8105 find /data -name 'records.parquet' -newer /data/SHFE.rb2605/1min/records.parquet -type f | wc -l"
# 预期：有新文件被修改（说明实时采集正在写入）
```

### 2.2 数据连贯性验证（2026-04-19 后）

```bash
# 检查 4月9日之后是否有新数据
curl "http://192.168.31.76:8105/api/v1/bars?symbol=KQ.m@SHFE.rb&start=2026-04-09&end=2026-04-18&interval=60" | python3 -c "import json,sys; d=json.load(sys.stdin); print(f'count={d.get(\"count\")}, latest={d.get(\"bars\",[[]])[-1][0] if d.get(\"bars\") else \"empty\"}')"
```

### 2.3 完整数据流端到端测试

```bash
# 1. 确认 Mini 数据可读
curl "http://192.168.31.76:8105/api/v1/bars?symbol=KQ.m@SHFE.rb&start=2026-04-15&end=2026-04-18&interval=60" 

# 2. 触发 Alienware 研究员
curl -X POST "http://192.168.31.223:8199/api/v1/researcher/run"

# 3. 验证报告生成
curl "http://192.168.31.223:8199/api/v1/researcher/reports?limit=5"

# 4. 确认飞书通知发送（观察飞书群）
```

### 2.4 数据覆盖范围确认

| 品种 | 4月1-8日 | 4月9-17日 | 预期恢复 |
|------|---------|----------|---------|
| SHFE.rb（螺纹钢） | ✅ 已回补 | ❌ 缺失 | 夜盘开始后逐步补全 |
| SHFE.hc（热卷） | ✅ 已回补 | ❌ 缺失 | 同上 |
| DCE.i（铁矿石） | ✅ 已回补 | ❌ 缺失 | 同上 |
| （共35品种） | ✅ | ❌ | 同上 |

---

## 3. 执行条件

- 夜盘（4月17日 21:00）开始后执行 §2.1 验证
- 次日（4月18日）早上验证 §2.2 数据连贯性  
- 数据连贯后执行 §2.3 完整流程验证
- 验证全通过后关闭本任务

---

## 4. 验收标准

- [ ] 4月17日夜盘数据（21:00-次日凌晨）成功写入
- [ ] 4月9-17日缺口通过实时采集逐步填补（不强求立即全补）
- [ ] `curl .../bars?symbol=KQ.m@SHFE.rb&start=2026-04-15...` 返回有效数据
- [ ] Alienware 研究员触发后生成 ≥1 份报告
- [ ] 飞书收到研究员通知

---

## 5. 注意事项

1. **不修改代码**：本任务只做验证，不涉及代码变更，无需 Token
2. **TqSdk 限制**：回测模式无法补历史近期数据，只能靠实时采集
3. **如果实时采集不写入**：重新排查 `pipeline.py` 的 `is_trading_time()` 逻辑

---

【建档者】Atlas  
【Token】暂不签发  
【执行时间】2026-04-17 21:00 后开始验证，2026-04-19 前完成
