# REVIEW-TASK-0035 data端 U0 新闻卡片排版与推送路由修复

## 文档信息

- 任务 ID：TASK-0035
- 审查类型：U0 事后快速审计
- 审查人：项目架构师（Atlas 代行）
- 审查时间：2026-04-10 13:10
- 设备：MacBook

---

## 一、U0 边界合规审查

| 检查项 | 结论 |
|--------|------|
| 仅限单服务 `services/data/**` | ✅ 通过 |
| 未触碰永久禁区 | ✅ 通过 |
| 无跨服务写入 | ✅ 通过 |
| 无目录新增 | ✅ 通过 |
| 无部署编排改动 | ✅ 通过 |
| 用户已确认运行态成功 | ✅ 通过 |

---

## 二、代码改动逐文件审查

### `card_templates.py`

- `SERVICE_NAME` 含 `BotQuant 资讯` → 解决飞书关键词验证失败问题，改动最小且必要。✅
- `alert_card` 标题前缀 `JBQ` → 仅为显示格式调整，无逻辑副作用。✅

### `news_pusher.py`

- `NotifyType.P0 → NotifyType.NEWS`：修复路由，Breaking 新闻应进资讯群，原 P0 路由为显式错误。✅
- `bypass_quiet_hours=True → False`：恢复正常静默时段过滤，符合设计预期。✅
- `BLACK_SWAN_KEYWORDS_ZH` 精简：删除的词均为泛义词（主席/总统/暴涨/暴跌等），保留的为真实高危词。✅
- 50 条上限 / 240 字截断：合理扩容，无逻辑风险。✅
- 统计行追加：只读操作，信息增益明确。✅

### `feishu.py`

- `_build_news_card()` 静态方法：与原 `alert_card` path 互不干扰，仅在 news 事件时走新路径。✅
- `send()` 路由分叉：条件清晰，不影响非 news 事件。✅
- 接口导入方式从 `card_templates` 内函数引用，无循环依赖风险。✅

---

## 三、运行态验证

| 验证项 | 结果 |
|--------|------|
| 手动 flush 测试 | `pushed:5, breaking_pushed:5, buffer_size:0` ✅ |
| 调度器 PID 82065 运行 | ✅ |
| `interval[0:03:00]` 确认 | ✅ |
| Mini 与 MacBook 文件大小一致 | ✅ |
| Git `84e441f` 推送 origin | ✅ |

---

## 四、审查结论

**PASS** — 本轮 U0 直修边界合规，代码改动合理，运行态验证充分，可进入锁回与账本收口。
