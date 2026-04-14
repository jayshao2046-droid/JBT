# REVIEW-TASK-0116 预审记录

| 字段 | 值 |
|------|-----|
| 预审ID | REVIEW-TASK-0116 |
| 任务 | TASK-0116 |
| 审核人 | Atlas（项目架构师代审） |
| 日期 | 2026-04-15 |
| 结论 | ✅ 通过 |

## 审核要点

### 1. 服务边界
- 所有修改限于 `services/decision/` 内部
- factor_miner.py / factor_validator.py / factor.py 均为新建文件

### 2. 安全性（因子代码沙箱）
- AI 提案模式 deepcoder 生成因子代码需在受限环境 eval
- 禁止 import os/sys/subprocess/shutil 等系统模块（白名单 eval）
- 沙箱失败返回 IC=0 拒绝注册，不抛异常到主进程

### 3. IC 计算
- 使用 Spearman 秩相关（scipy.stats.spearmanr），对异常值鲁棒
- IC 半衰期 < 3 日直接拒绝（避免短周期噪声因子污染注册表）

### 4. 数据驱动候选数量控制
- 候选组合上限 200 个（防止笛卡尔积爆炸）
- 超过上限时随机采样，保证运行时间可控

### 5. 保护级别
- P1（新建文件为主，单服务范围）

### 批次白名单
- `services/decision/src/research/factor_miner.py`（新建）
- `services/decision/src/research/factor_validator.py`（新建）
- `services/decision/src/api/routes/factor.py`（新建）
- `services/decision/tests/test_factor_mining.py`（新建）
