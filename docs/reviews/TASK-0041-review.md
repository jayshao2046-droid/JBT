# TASK-0041 预审记录

## 基本信息

| 字段 | 值 |
|------|-----|
| 任务编号 | TASK-0041 |
| 任务标题 | CTP前端下单/撤单UI + system/state密码脱敏 |
| 审核人 | 项目架构师（Atlas 代记录） |
| 审核日期 | 2026-04-10 |
| 审核结果 | ✅ 预审通过 |

---

## 预审检查清单

| # | 检查项 | 结果 | 说明 |
|---|--------|------|------|
| 1 | 服务归属明确 | ✅ | 仅 sim-trading 单服务 |
| 2 | 不涉及跨服务 | ✅ | 无跨服务 import 或写入 |
| 3 | 不涉及 shared/contracts | ✅ | 无契约变更 |
| 4 | 前置条件满足 | ✅ | CTP 已对接光大，代码已在工作树 |
| 5 | 验收标准明确 | ✅ | A 批编译通过 + B 批脱敏验证 |
| 6 | 安全审查 | ✅ | B 批专门修复密码明文泄漏 |
| 7 | 白名单范围合理 | ✅ | A 批 2 文件 + B 批 1 文件，最小必要 |

---

## 预审意见

1. A 批代码已由另一 session 编写完成，在工作树中未提交；本次走标准流程补签 Token 后正式提交。
2. B 批为 P0 安全修复：`/api/v1/system/state` 端点直接返回含 `ctp_password` 和 `ctp_auth_code` 的完整 `_system_state` 字典。该端点的 `get_ctp_config()` 已有脱敏逻辑，`get_system_state()` 需同样处理。
3. A 批和 B 批顺序固定：先 A（前端），后 B（后端安全）。B 批不依赖 A 批。
4. `.con` 文件清理（gitignore）可与任一批次并行处理，属于仓库卫生，不需要 Token。

---

## 白名单冻结

### A 批（P1，2 文件）

```
services/sim-trading/sim-trading_web/app/operations/page.tsx
services/sim-trading/sim-trading_web/lib/sim-api.ts
```

### B 批（P0，1 文件）

```
services/sim-trading/src/api/router.py
```

---

【签名】Atlas（代项目架构师记录）
【时间】2026-04-10 20:30
【设备】MacBook
