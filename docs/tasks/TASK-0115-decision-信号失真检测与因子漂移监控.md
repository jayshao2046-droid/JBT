# TASK-0115 — 决策端信号失真检测 + 因子漂移监控（G8）

【创建】2026-04-15
【服务归属】`services/decision/`
【执行 Agent】Claude-Code
【复核】Atlas
【状态】建档完成，待签发

## 任务概述

实装 G8 缺口：信号失真检测（预测 vs 实际对比）+ 因子漂移监控（PSI/KS 检验），出现失真或漂移时通过飞书 P1 报警并触发再训练标记，保障信号质量与因子时效性。

## 背景

当前没有任何机制检测：
- XGBoost 预测信号是否开始失准（信号失真）
- 因子分布是否因市场结构变化发生漂移（因子过期）
- 两者持续恶化时不会自动预警，只能人工发现后亡羊补牢

## 分批计划

### Batch A — 失真检测 + 漂移监控（P1，3 文件）

| 文件 | 操作 | 说明 |
|------|------|------|
| `services/decision/src/research/signal_validator.py` | 新建 | SignalValidator：30日滚动回测预测 vs 实际；准确率 < 阈值（默认55%）连续5日 → 飞书P1报警 + regime_retrain_flag=True |
| `services/decision/src/research/factor_monitor.py` | 新建 | FactorMonitor：KS 检验因子分布漂移（p < 0.05）+ PSI 指数（> 0.25）→ 飞书P1报警 + factor_status=deprecated；每日收盘后自动运行 |
| `services/decision/tests/test_signal_validator.py` | 新建 | 测试：失真超阈值触发报警、漂移检验通过/不通过、factor_status 状态转换 |

## 质量标准

- signal_validator 使用已有 DecisionFeishuNotifier 发 P1 报警（orange ⚠️）
- factor_monitor 持续追踪 factor_loader 中已注册的全部因子
- 报警消息格式：含品种、因子名、当前准确率/PSI、阈值、连续天数
- 测试 mock 验证不需要真实 Ollama 连接

## 依赖

- TASK-0114（ModelRegistry）完成后更有意义，但此任务自身可独立执行
- 使用已有 notifier/feishu.py，不新建通知模块
