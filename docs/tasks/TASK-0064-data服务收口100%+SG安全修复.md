# TASK-0064 — data 服务收口 100% + SG 安全修复（F-002/F-003）

【签名】Atlas  
【时间】2026-04-12  
【设备】MacBook  
【状态】� Token 已签发（tok-5b40deb2-eb21-4c5e-a857-94cbbca51c58，有效期 4320min）

## 任务基本信息

| 字段 | 内容 |
|------|------|
| 任务编号 | TASK-0064 |
| 任务名称 | data 服务收口 100% + SG 安全修复（F-002/F-003） |
| 所属阶段 | Round 1 冲刺 / SG 安全治理横线 |
| 主责服务 | `services/data/` |
| 协同服务 | 无 |
| 执行 Agent | Claude-Code |
| 优先级 | P0 |
| 前置依赖 | Round 0 全域只读安全扫描完成 |
| 状态 | 📋 待 Token 签发 |

## 任务背景

data 服务当前完成度 93%，存在两个遗留 STUB 和两个安全问题（F-002 subprocess 风险、F-003 查询构造链风险）。本任务目标：功能补全 → 93% 提升到 100%，同时完成 SG 安全修复。

## 文件级白名单（精确，共 6 项）

| # | 文件路径 | 改动目的 |
|---|---------|---------|
| 1 | `services/data/src/collectors/base.py` | 移除 A2 存储 STUB，完成存储层迁移 |
| 2 | `services/data/src/scheduler/data_scheduler.py` | 补全因子通知 STUB + 修复调度逻辑 |
| 3 | `services/data/src/health/health_check.py` | 修复 stock/news 健康检查误报 |
| 4 | `services/data/src/notify/dispatcher.py` | 增加因子/watchlist 通知路由 |
| 5 | `services/data/src/main.py` | 添加 API 认证中间件（SG 安全修复 F-002/F-003）|
| 6 | `services/data/tests/` 下相关测试文件 | 对应测试补全 |

> ⚠️ SG 安全修复（F-002/F-003）的 commit 必须独立于功能 commit，不得合并。

## 验收标准

- [ ] `pytest services/data/tests/ -x -q` 全量通过
- [ ] 健康检查接口无误报
- [ ] API 认证中间件生效（未授权请求返回 401）
- [ ] 存储层 STUB 已移除，实际写入可验证
- [ ] F-002/F-003 安全问题修复代码已独立 commit 并附代码证据

## 收口流程

1. Claude-Code 改动 → 写私有 prompt 留痕 → 独立 commit（功能/SG 分开）
2. 积累若干 commit 后 → Claude-Code 调用 `append_atlas_log`
3. Atlas 一次性审查 → Jay.S 确认 → push → Mini/Studio 两地同步
