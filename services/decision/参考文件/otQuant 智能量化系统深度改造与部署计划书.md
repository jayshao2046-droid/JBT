# 🚀 BotQuant 智能量化系统深度改造与原子级部署计划书

**版本：** v3.0 (Ultra-Detailed Implementation Plan)  
**日期：** 2026-04-06  
**适用设备：** Mac Studio (决策/交易/回测), Mac Mini (数据), MacBook (开发)  
**核心目标：** 构建“夜间自动训练 + 盘中实时推理 + 双重风控监管”的闭环系统

---

## 一、总体架构拓扑与数据流向详解

本系统采用微服务化加事件驱动架构，彻底解耦数据、计算与交易。所有通信均通过 FastAPI (HTTP REST) 进行，确保跨设备（Mini ↔ Studio）的低延迟与高可靠性。

### 1.1 物理节点职责划分（原子级）

**Mini (数据端)**
硬件配置为 M2 / 8G+SSD。核心进程包括 data_api (FastAPI)、data_scheduler (Cron) 和 health_monitor。关键端口为 8001 和 8899。存储路径绝对定位为 /Users/jaybot/J_BotQuant/BotQuan_Data/，其下包含 futures_minute/1m/KQ_m_*/（分钟线）、macro_global/（宏观数据）和 news_collected/（新闻数据）。严禁在此节点运行任何策略推理或直接连接 SimNow 交易接口。

**Studio (计算/交易端)**
硬件配置为 M2 Max / 32G。核心进程包括 decision_api (FastAPI)、trading_api (FastAPI)、backtest_engine (Script)、night_daemon (Cron) 和 ollama (Local Service)。关键端口为 8002、8003 和 11434。存储路径绝对定位为 /Users/jaybot/J_BotQuant/，其下包含 shared_models/xgb_*.json（模型共享目录）、strategies/approved/（已审核策略）和 .governance/audit_log.db（审计日志数据库）。严禁在此节点运行全量采集守护或直接读写 Mini 本地文件。

**MacBook (开发端)**
硬件配置为 M2 Pro。仅承载 VSCode + Copilot 和 Git Client。禁止承载任何生产服务。

### 1.2 核心数据流向（时序逻辑）

**T-1日 23:00 (夜间训练触发)**
night_daemon (Studio) 唤醒，读取 BotQuan_Data/futures_minute (从 Mini 拉取最新 Parquet)，启动 XGBoost Training Pipeline (16个独立进程)，生成 xgb_{symbol}_v{date}.json 并存入 shared_models/。随后 LLM Judge (DeepSeek 14B) 分析新模型 IC 值，若达标则更新 strategy_registry.json。

**T日 09:00 (盘中实时推理)**
Mini 推送新 K 线 (data_api:8001)，Studio decision_api:8002 接收。Factor Calculator 增量计算 31 因子，XGBoost Inference 加载内存模型 xgb_{symbol} 输出 prob。LLM Gate (L1/L2) 注入新闻摘要进行校验，Risk Checker 执行硬规则过滤。最终信号发送至 trading_api:8003，由 SimNow CTP 下单。

**T日 23:05 (反馈闭环)**
trading_api 写入当日成交明细至 SQLite，night_daemon 读取并计算当日 PnL/IC/胜率，写入 audit_log，供次日 LLM 复盘使用。

---

## 二、XGBoost 多模型矩阵部署规范（一品一策）

严禁使用单一通用模型。针对 16 个品种涵盖趋势与震荡两种截然不同的市场特性，实施独立建模、独立存储、独立热加载。

### 2.1 模型文件命名与存储规范
存储目录统一为 /Users/jaybot/J_BotQuant/shared_models/。命名格式严格遵循 xgb_{exchange}_{symbol}_{version}_{date}.json，例如 xgb_SHFE_rb_v2_20260406.json 或 xgb_DCE_m_v1_20260406.json。同时维护一个元数据文件 model_manifest.json，记录每个模型的训练时间、样本量、夏普比率及适用市场状态。

### 2.2 训练引擎核心逻辑
该脚本将在夜间被 night_daemon 调用。首先加载数据，输入为 symbol（如 rb），路径从 Mini 同步 BotQuan_Data/futures_minute/1m/KQ_m_SHFE_rb/*.parquet (最近 5 年)。预处理阶段自动处理换月跳空，计算 31 个基础因子 (MACD, RSI, Boll, ATR, Vol...)。标签构建 Target 为 future_return_30min (未来 30 分钟收益率方向: 1/-1/0)，并剔除涨跌停及夜盘开盘前 5 分钟噪音数据。

模型训练采用 XGBClassifier，参数设定为 max_depth=4, learning_rate=0.05, n_estimators=500, scale_pos_weight=auto (处理不平衡)。验证采用 TimeSeriesSplit (5折)，严格防止未来函数。早停机制设置为 early_stopping_rounds=50，监控 validation-logloss。模型评估与保存阶段，若 OOS Sharpe > 1.0 且 IC > 0.03，则保存为 JSON，否则丢弃并记录日志。

### 2.3 推理引擎核心逻辑
该模块常驻内存，随 decision_api 启动。初始化时扫描 shared_models/ 目录，加载所有 xgb_*.json 到内存字典 self.models = {'rb': model_obj, 'm': model_obj, ...}。热加载机制通过监听目录文件变化 (watchdog) 实现，一旦检测到新版本（文件名版本号增加），自动卸载旧模型，加载新模型，无需重启服务。预测时输入 symbol 和 features_vector (31维 numpy array)，路由至 model = self.models.get(symbol)，若不存在则 Fallback 到规则策略，输出 probability (0.0 - 1.0) 和 confidence_class (High/Medium/Low)。

---

## 三、DeepSeek 14B 大模型监管与辅助体系

利用 Studio 本地 Ollama 部署的 deepseek-r1:14b，构建“夜间研究员”与“盘中风控官”双角色。

### 3.1 角色 A：夜间研究员 (Night Researcher)
触发时间为每日 23:10 (训练完成后)。输入数据包括今日交易日志 (JSON，含每笔信号的 entry_price, exit_price, pnl, signal_source)、模型性能报告 (IC_trend, WinRate_rolling_5d, MaxDrawdown_today) 以及市场新闻摘要 (从 BotQuan_Data/news_collected/ 提取的 Top 5 相关新闻标题)。

System Prompt 模板设定为：“你是一位资深量化风控专家。请分析以下 XGBoost 模型今日表现：[插入 JSON 数据]。任务：1. 判断模型是否失效（IC 是否显著下降？是否出现连续同向亏损？）。2. 结合新闻，分析是“短期噪音”还是“风格切换”。3. 给出明确指令：[KEEP], [REDUCE_RISK], 或 [DISABLE]。4. 若 DISABLE，简述理由（不超过 50 字）。输出格式：纯 JSON {"action": "...", "reason": "...", "risk_level": "Low/Med/High"}”。

执行动作解析 LLM 返回的 JSON。若 action == "DISABLE"，自动修改 configs/stage_presets.yaml 中对应品种状态为 disabled，并发送 P0 飞书告警。若 action == "REDUCE_RISK"，自动调整次日仓位系数 (如 position_multiplier = 0.5)。

### 3.2 角色 B：盘中风控官 (Real-time Gatekeeper)
触发条件为仅当 XGBoost 输出 confidence > 0.7 (高确信) 且 预计开仓金额 > 账户 2% 时异步触发。输入数据包括 XGBoost 信号详情、实时新闻流 (最近 1 小时) 以及宏观数据快照 (VIX, 汇率波动)。逻辑上 LLM 快速审查是否存在未量化的突发风险（如“突发战争”、“交易所公告”）。若发现重大利空，返回 REJECT，交易端立即撤销挂单或强平。超时控制严格限制 timeout=15s，超时默认 PASS (不阻塞交易)。

---

## 四、双重风控体系实施细则

建立“代码硬规则 (实时)” + “AI 软逻辑 (延时)”的双重防线。

### 4.1 硬规则引擎
运行在 trading_api 进程中，毫秒级响应，拥有最高优先级（一票否决权）。规则包括：HR-01 单笔最大风险 (账户权益 0.5%，拒绝开仓)；HR-02 日内累计亏损 (账户权益 2.0%，全局熔断，停止所有新开仓，次日 09:00 自动重置)；HR-03 连续亏损次数 (同品种 5 笔，品种级熔断，暂停该品种，30 分钟后自动尝试恢复)；HR-04 保证金占用率 (> 70% 禁止开新仓，< 60% 自动解除)；HR-05 网络延迟 (> 500ms 持续 10s，紧急强平所有持仓，网络恢复正常 + 人工确认)；HR-06 数据源中断 (> 30s 无新 K 线，停止交易 + 报警，数据恢复后人工重启)。

### 4.2 软逻辑监管
运行在 night_daemon 中，由 LLM 驱动，关注长期健康度。监控指标包括 IC Decay (滚动 20 日 IC 均值跌破 0.02)、PSI (Population Stability Index，当前输入因子分布与训练集分布差异 > 0.25) 以及 Regime Shift (市场波动率分位数发生剧烈跳变)。处置流程为检测到异常触发 LLM 深度分析，生成《模型健康诊断报告》，建议重训则自动触发 xgb_trainer.py 进行增量更新，建议停用则更新配置并告警。

---

## 五、一键部署与自动化运维脚本规范

为确保方案可落地，我们将所有配置、脚本、守护进程标准化，并通过一个主部署脚本 (deploy_full_stack.sh) 一键执行。

### 5.1 目录结构标准化
根目录 ~/J_BotQuant/ 下包含 configs/ (存放 stage_presets.yaml, futures_symbol_map.yaml, ai_engine.yaml)、scripts/ (存放 deploy_full_stack.sh, backfill_history.py, xgb_trainer.py, night_daemon.py, health_check.py)、src/ (包含 decision/, trading/, backtest/, risk/ 四个子模块)、shared_models/ (模型共享目录，挂载点) 以及 BotQuan_Data/ (数据目录，Mini 端)。

### 5.2 主部署脚本逻辑流
该脚本将在 Studio 和 Mini 上分别运行（通过参数区分角色）。首先进行环境检查，确认 Python 3.9+, Docker, Ollama, Git 是否安装，检查 .env 文件是否存在，缺失则从 .env.example 复制并提示填写 Key。接着进行依赖安装，执行 pip install -r requirements.txt (包含 xgboost, tqsdk, fastapi, ollama, pandas)，并拉取 Ollama 模型 ollama pull deepseek-r1:14b。

随后进行目录初始化，创建 shared_models/, logs/, BotQuan_Data/ 等目录，并设置权限 chmod 777 shared_models (确保容器间可写)。接着注册守护进程，复制 plist 文件到 ~/Library/LaunchAgents/，执行 launchctl load -w 注册 night_daemon, decision_api, trading_api。最后进行连通性测试，Ping Mini IP，Curl localhost:8002/health 和 localhost:8003/health，模拟一次 XGBoost 推理请求验证延迟 < 50ms，并输出绿色成功标志显示所有服务状态。

---

## 六、实施路线图与验收标准

### Phase 1: 数据基建与模型训练 (Day 1-2)
任务为运行 backfill_history.py 补全 5 年分钟线，首次运行 xgb_trainer.py 生成 16 个初始模型。验收标准为 shared_models/ 下有 16 个 .json 文件，Parquet 数据完整性 > 99%。

### Phase 2: 决策链路联调 (Day 3)
任务为启动 decision_api，接入 XGBoost 推理，配置 LLM Prompt 模板。验收标准为模拟行情输入能在 100ms 内输出带置信度的信号，LLM 能正确解析并返回 JSON。

### Phase 3: 风控与夜间闭环 (Day 4)
任务为部署 hard_rules 和 night_daemon，配置飞书告警。验收标准为模拟连续亏损 5 笔系统自动熔断，夜间自动运行训练并生成报告。

### Phase 4: 实盘模拟演练 (Day 5)
任务为连接 SimNow，进行 24 小时无人值守模拟运行。验收标准为零崩溃，零漏单，风控规则准确触发，早报准时推送。

---

## 七、风险控制与应急预案

模型失效应急：若 XGBoost 连续 3 日 IC < 0，自动回滚至上一版本模型，并切换至纯规则模式 (YAML)。LLM 服务宕机：若 Ollama 无响应，自动跳过 LLM 门控，仅依赖 XGBoost + 硬规则（降级运行）。数据中断应急：若 Mini 断连 > 30s，决策端自动进入“只平仓不开仓”模式，并报警。资金安全：所有实盘操作必须经过 HR-02 (日亏 2%) 硬熔断，且必须有飞书二次确认（实盘阶段）。

---

## 八、结语

本计划书已经将逻辑细化到了代码级和执行级。它不仅定义了“做什么”，更明确了“怎么做”、“在哪做”以及“失败了怎么办”。接下来，只需按照此蓝图，让 AI Agent 生成具体代码并执行 deploy_full_stack.sh，即可构建出这套强大的智能量化系统。祝您的 BotQuant 系统运行顺利，收益长虹！