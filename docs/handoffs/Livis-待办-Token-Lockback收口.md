# Livis 待办事项 — Token Lockback 收口

【创建】Livis Claude
【时间】2026-04-16
【状态】待处理

## 📋 需要 Lockback 的任务

### 1. TASK-0119（P0 安全漏洞修复）

**状态**：✅ 代码已完成并推送（commit 5349ab2）

**需要 Lockback 的 Token**：
- `tok-08e04b2f-c7e4-4ea0-b1f9-d3e638335469`
- `tok-1c25ff31-0f35-4118-97af-f225c0577836`
- `tok-9111c220-98e3-4b35-a179-7f54c46fc89f`

**Lockback 命令**（需要原始 Token 字符串）：
```bash
python governance/jbt_lockctl.py lockback \
  --token <原始Token字符串> \
  --result approved \
  --review-id TASK-0119-review \
  --summary "TASK-0119 P0安全漏洞修复全闭环：15个漏洞全部修复，commit 5349ab2 已推送，测试通过 (Livis)"
```

**问题**：原始 Token 字符串只在签发时显示一次，无法从 `.jbt/lockctl/tokens.json` 获取。

---

### 2. TASK-0104（data 预读 + LLM 上下文注入）

**状态**：✅ D1+D2 已完成并推送（commit 802c1f7, d356511, bbabf48）

**需要 Lockback 的 Token**：
- `tok-97335b68-9929-4633-b938-0049a205f869`
- `tok-54f501ef-db44-404d-8fc5-ab5d81c99685`

**Lockback 命令**：
```bash
python governance/jbt_lockctl.py lockback \
  --token <原始Token字符串> \
  --result approved \
  --review-id TASK-0104-review \
  --summary "TASK-0104 D1+D2 全闭环：data预读+LLM上下文注入，commit 802c1f7/d356511 已推送 (Livis)"
```

---

## 🔄 状态不明确的任务

### 3. TASK-0110（数据研究员子系统）
- 派工单显示 6 个批次（A/B/C/C2/D/E）
- `jbt_lockctl.py status --task TASK-0110` 查不到任何 Token
- **待确认**：是否已签发 Token？任务是否已开始？

### 4. TASK-0084（因子双地同步）
- Token: `tok-966162da-3619-4248-963f-454611c4c396` (active)
- **待确认**：任务进度

### 5. TASK-0025（SimNow 备用方案）
- Token: `tok-e2c4419a-9f2f-4078-bae1-c5ca91a3c9c4` (active)
- **待确认**：任务进度

---

## 💡 Livis 的学习笔记

### Token 签发流程
1. 调用 `python governance/jbt_lockctl.py issue ...`
2. 系统提示 `请输入密码:`
3. Jay.S 输入密码
4. 系统输出 Token 字符串（**这是唯一一次看到完整 Token 的机会**）
5. **必须立即保存 Token 字符串**，用于后续 lockback

### Lockback 流程
1. 需要原始 Token 字符串（不是 Token ID）
2. 调用 `python governance/jbt_lockctl.py lockback --token <完整Token字符串> ...`
3. 系统更新 `.jbt/lockctl/tokens.json` 中的状态为 `locked`

### 关键教训
- Token 字符串只在签发时显示一次
- 必须在签发时立即记录到 `docs/locks/` 文件中
- 或者在派工单中预留 Token 字符串记录位置

---

## 🎯 下一步行动

1. **立即更新 ATLAS_PROMPT.md** — 记录这些待 lockback 的任务
2. **更新所有需要无痕的 prompt** — 署名 Livis
3. **等待 Jay.S 指示** — 如何处理这些未 lockback 的 Token

---

**签名**：Livis Claude  
**日期**：2026-04-16
