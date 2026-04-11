# Atlas To Qwen Phase C Step 1

## 目标
将 Phase C 从"总计划冻结态"整理成"可执行拆批底稿"。

## 范围与方法
1. 盘清 Phase C 全量事项：`C0 / CA / CB / CG / CF / CS / CK`
2. 给每个事项补齐真实仓库锚点、依赖关系、主责服务、主要缺口
3. 保留当前总控约束：`Phase C` 现在仍处于"待拆批 / 待预审 / 待签发"状态，不能直接等同于代码授权
4. 若事项涉及跨服务、`shared/contracts/**`、`shared/python-common/**`、`.github/**`、`docker-compose.dev.yml`、任一 `.env.example`，必须明确标注"需项目架构师预审 + Token"

## Phase C 全量清单矩阵

### C0 共享前置
| 编号 | 任务 | 主责 | 协同 | 验收标准 | 仓库锚点 | 状态 | 依赖 | 主要缺口 |
|------|------|------|------|---------|----------|------|------|----------|
| C0-1 | 股票 bars API 路由扩展 | 数据 | 决策 | `services/data/src/main.py` 支持股票代码解析与 `stock_daily/stock_minute` 供数 | `services/data/src/main.py` | 待实施 | 无 | 股票路由层未实现 |
| C0-2 | FactorLoader 股票代码支持 | 决策 | 数据 | `factor_loader.py` 可通过 data API 拉取股票日线/分钟K | `services/decision/src/research/factor_loader.py` | 待实施 | C0-1 | FactorLoader 缺股票数据拉取能力 |
| C0-3 | 策略导入解析器 | 决策 | 无 | 统一支持看板 YAML / 邮件 YAML / 内部生成策略的入库与校验 | `services/decision/src/publish/strategy_importer.py` | 待实施 | 无 | 策略导入解析器未实现 |

### CA 期货研究链路
| 编号 | 任务 | 主责 | 协同 | 验收标准 | 仓库锚点 | 状态 | 依赖 | 主要缺口 |
|------|------|------|------|---------|----------|------|------|----------|
| CA1 | 看板导入与研究入口 | 决策 | 无 | `research-center` 可导入期货策略并登记到策略仓库 | `services/decision/src/research/` + `decision_web/` | 待实施 | 无 | 期货策略导入UI未实现 |
| CA2' | 期货沙箱回测引擎 | 决策 | 数据 | decision 内部完成期货逐 bar 回测与绩效统计，不依赖 backtest API | `services/decision/src/research/futures_sandbox.py` | 待实施 | C0-2 | 期货沙箱回测引擎未实现 |
| CA3 | 回测报告展示与导出 | 决策 | 无 | 研究中心页面可展示并导出期货回测报告 | `services/decision/src/research/report_generator.py` + `decision_web/` | 待实施 | CA2' | 期货回测报告生成与展示未实现 |
| CA4 | 交易参数调优引擎 | 决策 | 无 | 基于真实 Sharpe / 回撤等指标调优期货交易参数 | `services/decision/src/research/optimizer.py` | 待实施 | CA2' | 参数调优引擎未实现 |
| CA5 | 期货研究中心全流程 UI | 决策 | 无 | 页面闭环覆盖导入、回测、调优、报告、提交人工复核 | `decision_web/` | 待实施 | CA1-CA4 | 期货研究中心完整UI未实现 |
| CA6 | 信号真闭环 → sim-trading | 决策 | 模拟交易 | 通过人工二次回测确认后，策略可进入 sim-trading 执行 | `services/decision/src/publish/sim_adapter.py` | 待实施 | CG2 | 与sim-trading的信号闭环未实现 |
| CA7 | PBO过拟合检验 | 决策 | 无 | 研究报告输出 PBO/CPCV，作为自动研发门禁的一部分 | `services/decision/src/research/pbo_validator.py` | 待实施 | CA2' | PBO/CPCV验证器未实现 |

### CB 股票研究链路
| 编号 | 任务 | 主责 | 协同 | 验收标准 | 仓库锚点 | 状态 | 依赖 | 主要缺口 |
|------|------|------|------|---------|----------|------|------|----------|
| CB1 | 股票策略模板（短/中/长期） | 决策 | 无 | 形成面向日线的 short/mid/long 三类模板 | `services/decision/src/research/templates/` | 待实施 | 无 | 股票策略模板未定义 |
| CB2' | 股票沙箱回测引擎 | 决策 | 数据 | decision 内部完成股票日线回测，不依赖 backtest 自动引擎 | `services/decision/src/research/stock_sandbox.py` | 待实施 | C0-2 | 股票沙箱回测引擎未实现 |
| CB3 | 全 A 股选股引擎 + benchmark | 决策 | 数据 | 先完成全量跑分 benchmark，再冻结每日固定选股时间 | `services/decision/src/research/stock_picker.py` | 待实施 | CB2' | 全A股选股引擎未实现 |
| CB4 | 股票池管理器 | 决策 | 无 | 白天/晚间轮换后池内常驻 30 只股票，保留淘汰理由 | `services/decision/src/research/stock_pool_manager.py` | 待实施 | CB3 | 股票池管理器未实现 |
| CB5 | 动态 watchlist 分钟K采集 | 数据 | 决策 | data 端按 20 只 watchlist 动态采集分钟 K，替代全量轮询 | `services/data/src/collectors/stock_minute_collector.py` | 待实施 | C0-1 | 动态watchlist采集未实现 |
| CB6 | 盘中跟踪与飞书入离场提醒 | 决策 | 数据 | 盘中基于分钟 K 给出入场/离场提醒 | `services/decision/src/notify/trade_signals.py` | 待实施 | CB5 | 盘中跟踪与提醒未实现 |
| CB7 | 盘后评估与未来预判 | 决策 | 无 | 对 30 只股票输出走势评估、目标价位、止盈止损与预判 | `services/decision/src/research/post_market_analysis.py` | 待实施 | CB4 | 盘后评估未实现 |
| CB8 | 晚间再选 + 淘汰 + 报告 | 决策 | 无 | 每晚新增 20、淘汰 10、保留 10，并输出完整报告 | `services/decision/src/research/evening_rebalancer.py` | 待实施 | CB7 | 晚间再选与报告未实现 |
| CB9 | 股票研究中心页面 | 决策 | 无 | 看板显示股票池、入离场时间线、选股排行与盘后评估 | `decision_web/` | 待实施 | CB1-CB8 | 股票研究中心完整UI未实现 |

### CG 人工二次回测关卡
| 编号 | 任务 | 主责 | 协同 | 验收标准 | 仓库锚点 | 状态 | 依赖 | 主要缺口 |
|------|------|------|------|---------|----------|------|------|----------|
| CG1 | 回测端策略导入队列 | 回测 | 决策 | backtest 端可导入"原始策略 / 研究中心优化后策略" | `services/backtest/src/api/routes/strategy.py` | 待实施 | 无 | 回测端策略导入未实现 |
| CG2 | 人工手动回测 + 审核确认 | 回测 | 决策 | 人工点选回测、审阅结果、确认是否启用，回写 decision 状态 | `services/backtest/src/backtest/manual_runner.py` + `backtest_web/` | 待实施 | CG1 | 人工手动回测与审核流程未实现 |
| CG3 | 回测端股票手动回测与看板调整 | 回测 | 数据 | 回测端新增股票回测与对应看板页面 | `services/backtest/src/backtest/stock_backtester.py` + `backtest_web/` | 待实施 | CG2 | 股票手动回测功能未实现 |

### CF 导入通道
| 编号 | 任务 | 主责 | 协同 | 验收标准 | 仓库锚点 | 状态 | 依赖 | 主要缺口 |
|------|------|------|------|---------|----------|------|------|----------|
| CF1' | 飞书口头策略通道 | 决策 | 无 | 用户可用自然语言提出策略想法，研究中心自动生成策略并反馈结果 | `services/decision/src/notify/feishu_bot.py` + `services/decision/src/research/nlp_strategy_generator.py` | 待实施 | 无 | 飞书NLP策略生成未实现 |
| CF2 | 邮件 + 看板 YAML 导入 | 决策 | 无 | YAML 仅允许标准格式邮件或看板上传；导入成功/失败通过飞书通知 | `services/decision/src/publish/yaml_importer.py` + `decision_web/` | 待实施 | C0-3 | 邮件/YAML导入与通知未实现 |

### CS 容灾与断联接管
| 编号 | 任务 | 主责 | 协同 | 验收标准 | 仓库锚点 | 状态 | 依赖 | 主要缺口 |
|------|------|------|------|---------|----------|------|------|----------|
| CS1 | decision 本地 Sim 容灾引擎 | 决策 | 模拟交易/实盘交易 | 平时 standby；一旦与正式交易端断联，即可本地接管任务与临时账本 | `services/decision/src/failover/local_sim_handler.py` | 待实施 | 无 | 本地容灾引擎未实现 |
| CS1-S | 交易端交接接口 | 模拟交易 | 决策/实盘交易 | 正式交易端恢复后可接收订单/持仓/账本差异并完成任务回切 | `services/sim-trading/src/api/routes/failover.py` | 待实施 | CS1 | 交接接口未实现 |

### CK 因子体系
| 编号 | 任务 | 主责 | 协同 | 验收标准 | 仓库锚点 | 状态 | 依赖 | 主要缺口 |
|------|------|------|------|---------|----------|------|------|----------|
| CK1 | 共享因子库覆盖率扩充 | 决策+回测 | 项目架构师 | 共享因子覆盖率达到 90%+，大多数导入策略无需单独补因子 | `shared/python-common/src/factors/` | 待实施 | 无 | 因子库覆盖率不足 |
| CK2 | 因子双地同步与版本校验 | 项目架构师 | 决策+回测 | 研究中心与回测端因子实现、版本、hash 保持一致 | `shared/python-common/src/factors/` + `services/decision/src/research/` + `services/backtest/src/backtest/` | 待实施 | CK1 | 因子双地同步机制未实现 |
| CK3 | 因子缺失/新增通知 | 决策+回测 | 无 | 导入缺失因子或研究中心新增因子时，双端都能通知并留痕 | `services/decision/src/research/factor_notifier.py` + `services/backtest/src/backtest/factor_notifier.py` | 待实施 | CK2 | 因子通知机制未实现 |

## 并行关系与依赖分析
- `C0-1 ⊥ C0-3 -> C0-2`：C0-1和C0-3可并行，完成后C0-2才能开始
- `CA2' ⊥ CB2'`：期货沙箱和股票沙箱可并行开发
- `CA/CB` 的自动研究结果统一汇入 `CG1/CG2/CG3` 人工二次回测关卡
- `CK1 -> CK2 -> CK3` 贯穿决策与回测两端
- `CS1/CS1-S` 与双沙箱可并行推进

## 已有基础能力盘点
- `services/decision/src/research/`：现有骨架已存在
- `services/decision/src/model/router.py`：模型路由骨架已存在
- `services/data/src/collectors/stock_minute_collector.py`：股票分钟线采集器已存在，但默认关闭
- `services/backtest/src/backtest/engine_router.py`：回测引擎路由已存在
- `services/backtest/src/backtest/risk_engine.py`：风控引擎已存在

## 特殊标注事项
- CK2/CK3 涉及 `shared/python-common/**`，需项目架构师预审 + Token
- CS1-S 涉及跨服务API，需项目架构师预审 + Token
- 任何涉及 `shared/contracts/**` 的事项需项目架构师预审 + Token
- 所有跨服务协同需项目架构师预审 + Token