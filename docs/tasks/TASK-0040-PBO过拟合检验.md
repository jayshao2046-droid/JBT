# TASK-0040 PBO 过拟合检验

## 文档信息

- 任务 ID：TASK-0040
- 文档类型：新任务建档
- 签名：Atlas
- 建档时间：2026-04-10
- 设备：MacBook
- 原编号：TASK-0037（因 U0 通知降噪修复占用该编号，重新编号为 TASK-0040）

---

## 一、任务目标

在决策端内置研究回测引擎中实现 PBO（Probability of Backtest Overfitting）过拟合检验能力，为策略发布提供统计学验证门禁。

**核心交付物：**

1. CPCV 多折验证引擎（基于 mlfinlab `combinatorial_purged_cross_val`）
2. PBO Score 计算（基于 mlfinlab `probability_of_backtest_overfitting`）
3. 研究报告 JSON 输出（含 PBO Score + CPCV 折叠报告）
4. decision_web 模型因子页 PBO 可视化（PBO ≤ 0.5 绿 / > 0.5 红）

---

## 二、服务归属与边界判定

### 归属结论

- **任务归属：`services/decision/` 决策端单服务范围**
- 基于决策端内置研究回测引擎，不依赖 Air 人工回测端
- 不涉及 `services/backtest/` 代码

### 依赖

| 依赖项 | 状态 |
|--------|------|
| Phase C C2（策略研发中心基础） | 🔲 待实施 |
| mlfinlab 库可用 | 🔲 待确认 |
| decision_web 因子页基础 | 🔲 待实施 |

---

## 三、技术方案

### 3.1 CPCV 验证引擎

- 输入：策略收益序列 + 因子数据
- 方法：Combinatorial Purged Cross-Validation（CPCV）
- 依赖：`mlfinlab.cross_validation.combinatorial_purged_cross_val`
- 输出：多折验证绩效矩阵

### 3.2 PBO Score

- 输入：CPCV 多折绩效矩阵
- 方法：`mlfinlab.backtest_statistics.probability_of_backtest_overfitting`
- 输出：PBO Score（0~1，越低越好）
- 门禁规则：PBO ≤ 0.5 通过（绿），PBO > 0.5 拒绝（红）

### 3.3 决策门禁集成

- AI 自动研发策略发布前必须满足：
  1. flake8 + bandit 扫描通过
  2. 沙箱容器资源限制验证通过
  3. PBO Score ≤ 0.5

---

## 四、验收标准

| # | 验收项 | 判定方式 |
|---|--------|---------|
| 1 | CPCV 引擎可对任意策略执行多折验证 | 单元测试 + 示例策略验证 |
| 2 | PBO Score 正确输出到研究报告 JSON | JSON schema 验证 |
| 3 | decision_web 因子页显示 PBO 色标 | 页面截图验证 |
| 4 | 策略发布门禁拦截 PBO > 0.5 | 集成测试 |

---

## 五、执行计划

> 注：本任务依赖 Phase C C2（研发中心）完成后才能启动实施

1. **A0 — 建档**：创建 task/review/lock 文件（本步骤）✅
2. **A1 — mlfinlab 集成**：安装并验证 mlfinlab 可用性
3. **A2 — CPCV 引擎实现**：在 decision 端实现 CPCV 验证模块
4. **A3 — PBO 计算**：实现 PBO Score 计算并输出到研究报告
5. **A4 — Web 展示**：decision_web 因子页 PBO 色标展示
6. **A5 — 门禁集成**：策略发布流程集成 PBO 检查

---

## 六、风险评估

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| mlfinlab 许可证限制 | 高 | 确认 BSD 许可证兼容性 |
| CPCV 计算耗时 | 中 | 异步任务 + 缓存结果 |
| C2 研发中心延期 | 中 | 本任务延后，不影响其他 Phase |

---

【签名】Atlas
【时间】2026-04-10
【设备】MacBook
