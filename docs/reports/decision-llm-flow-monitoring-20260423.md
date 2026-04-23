# Decision LLM 流程监控报告

**监控时间**: 2026-04-23  
**监控对象**: Studio Decision (192.168.31.142:8104)  
**监控周期**: 部署后 5 分钟

---

## 一、部署状态确认

### 1.1 服务状态

| 指标 | 状态 | 说明 |
|------|------|------|
| 容器运行 | ✅ | Up (healthy) |
| 健康检查 | ✅ | /health 返回 200 OK |
| 应用启动 | ✅ | Application startup complete |
| 研究员评级 | ✅ | /api/v1/evaluate 正常响应 |

### 1.2 修复验证

| 修复项 | 验证方法 | 状态 | 备注 |
|--------|---------|------|------|
| TTL 12h | 观察缓存刷新日志 | ⏳ 待观察 | 需等待首次缓存刷新 |
| 研报 404 WARNING | 检查日志级别 | ⏳ 待触发 | 需等待研报 API 404 场景 |
| tqsdk 配置检查 | 检查 WARNING 日志 | ⏳ 待触发 | 需等待 K 线拉取场景 |
| 时间清理 | 检查 JSON 文件 | ⏳ 待观察 | 需等待新评级保存 |

---

## 二、日志分析

### 2.1 启动日志

```
INFO:     Started parent process [1]
INFO:     Started server process [8]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Started server process [9]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**分析**: 双进程启动正常，应用初始化完成。

### 2.2 运行日志

```
INFO:     180.163.146.10:43593 - "GET /health HTTP/1.1" 200 OK
INFO:     127.0.0.1:52998 - "GET /health HTTP/1.1" 200 OK
MODEL_PRICES 未设置，计费将使用默认估算价格
[SCORER] 标记已读失败: NEWS-20260423-11, Client error '404 Not Found'
INFO:     180.163.146.10:39601 - "POST /api/v1/evaluate HTTP/1.1" 200 OK
```

**分析**:
- ✅ 健康检查正常
- ℹ️ 计费提示（非错误，仅提示）
- ℹ️ Alienware `/mark_read` 端点 404（非关键功能）
- ✅ 研究员评级正常响应

---

## 三、待观察项

### 3.1 TTL 缓存（12 小时）

**观察目标**: 
- 首次缓存加载时间
- 缓存命中日志
- 12 小时内是否走缓存

**观察方法**:
```bash
ssh jaybot@192.168.31.142 'docker logs JBT-DECISION-8104 --since 1h | grep -E "(DailyContextLoader|TTL|缓存)"'
```

**预期行为**:
- 首次请求：`正在从 data 服务拉取预读上下文`
- 后续请求：`返回缓存的预读上下文 (TTL 内)`

---

### 3.2 研报 404 告警

**观察目标**: 
- L2 审查时研报缺失日志级别
- 是否为 WARNING 级别

**观察方法**:
```bash
ssh jaybot@192.168.31.142 'docker logs JBT-DECISION-8104 --since 1h | grep -E "(L2 上下文|研报 API|404)"'
```

**预期行为**:
- 旧版本：`logger.info(f"L2 上下文：研报 API 未就绪 (404)")`
- 新版本：`logger.warning(f"L2 上下文：研报 API 未就绪 (404)")`

---

### 3.3 tqsdk 配置检查

**观察目标**: 
- tqsdk 账号未配置时的日志
- 是否明确提示环境变量名称

**观察方法**:
```bash
ssh jaybot@192.168.31.142 'docker logs JBT-DECISION-8104 --since 1h | grep -E "(tqsdk|KLINE|TQSDK_AUTH)"'
```

**预期行为**:
- 未配置时：`[KLINE] tqsdk 账号未配置（TQSDK_AUTH_USERNAME/PASSWORD 环境变量缺失），跳过实时 K 线拉取`

---

### 3.4 ResearchStore 时间清理

**观察目标**: 
- `runtime/research_store/*.json` 文件大小
- 超过 7 天的记录是否被清理

**观察方法**:
```bash
ssh jaybot@192.168.31.142 'docker exec JBT-DECISION-8104 ls -lh /app/runtime/research_store/'
ssh jaybot@192.168.31.142 'docker exec JBT-DECISION-8104 cat /app/runtime/research_store/macro.json | python3 -m json.tool | grep stored_at | head -5'
```

**预期行为**:
- 每次保存时执行时间清理
- 超过 7 天的记录被过滤
- JSON 文件大小保持稳定

---

## 四、监控计划

### 4.1 短期监控（24 小时）

| 时间点 | 监控项 | 方法 |
|--------|--------|------|
| 部署后 1h | TTL 缓存首次加载 | 检查日志 |
| 部署后 4h | 研报 404 告警 | 检查日志级别 |
| 部署后 12h | TTL 缓存刷新 | 检查缓存命中 |
| 部署后 24h | 时间清理效果 | 检查 JSON 文件 |

### 4.2 中期监控（1 周）

| 监控项 | 频率 | 指标 |
|--------|------|------|
| TTL 缓存命中率 | 每日 | 缓存命中次数 / 总请求次数 |
| 研报 404 频率 | 每日 | WARNING 日志出现次数 |
| ResearchStore 大小 | 每日 | JSON 文件总大小 |
| Ollama 降级频率 | 每日 | 在线 API 调用次数 |

---

## 五、问题与建议

### 5.1 已发现问题

| # | 问题 | 严重度 | 建议 |
|---|------|--------|------|
| 1 | Alienware `/mark_read` 404 | P2 | 非关键功能，可后续修复 |
| 2 | `MODEL_PRICES` 未设置 | P2 | 补充环境变量或使用默认值 |

### 5.2 优化建议

1. **增加监控指标**
   - L1/L2 审查通过率
   - 平均审查耗时
   - 数据降级频率

2. **日志增强**
   - TTL 缓存命中时记录 DEBUG 日志
   - ResearchStore 清理时记录清理数量

3. **告警规则**
   - 研报 404 连续 10 次触发 P1 告警
   - TTL 缓存失效率 > 50% 触发 P2 告警

---

## 六、总结

### 6.1 部署状态

✅ **部署成功**: 5 项修复已全部部署到 Studio Decision  
✅ **服务正常**: 容器运行正常，健康检查通过  
⏳ **待验证**: TTL 缓存、研报 404、tqsdk 配置、时间清理需持续观察  

### 6.2 下一步行动

1. **立即**: 持续观察日志，等待首次 TTL 缓存加载
2. **1 小时后**: 检查 TTL 缓存命中情况
3. **4 小时后**: 检查研报 404 告警级别
4. **24 小时后**: 生成完整监控报告

---

**报告生成时间**: 2026-04-23  
**报告人**: Atlas  
**下次更新**: 2026-04-24（24 小时后）
