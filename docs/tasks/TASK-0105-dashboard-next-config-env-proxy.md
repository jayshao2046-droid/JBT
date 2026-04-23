# TASK-0105: Dashboard next.config.ts — API proxy 支持环境变量

**状态**：active  
**服务**：services/dashboard/dashboard_web  
**执行端**：Atlas  
**日期**：2026-04-14

---

## 背景

Studio 部署后 dashboard 的 API proxy 全部指向 `localhost`，但：
- sim-trading:8101 主力在 Mini（192.168.31.156），Studio 上为容灾备份
- data:8105 在 Mini（192.168.31.156）

需要让 `next.config.ts` 支持读环境变量覆盖各服务地址，Studio 通过 `.env.local`（不进 git）指向 Mini，MacBook 开发默认 localhost 不受影响。

## 文件白名单

| 文件 | 操作 |
|------|------|
| `services/dashboard/dashboard_web/next.config.ts` | 修改：4 个 proxy destination 改为读 env var，默认 localhost |

## 验收标准

1. MacBook 本地 `pnpm build` 通过
2. Studio 上配置 `.env.local` 后重启，`/api/sim-trading/health` 和 `/api/data/health` 返回 200
3. 不改变 decision/backtest 的默认行为
