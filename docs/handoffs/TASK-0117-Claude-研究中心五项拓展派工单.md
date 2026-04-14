# TASK-0117 Claude 派工单 — 决策端研究中心 5 项拓展

【任务ID】TASK-0117  
【服务】`services/decision/`  
【Token】`tok-f8d27abe-32ad-4b21-beae-fe03e6596ba7`  
【执行人】Claude-Code  
【复核人】Atlas  
【前置条件】TASK-0112 Batch C 完成后执行（依赖 `pipeline.full_pipeline()`）

---

## 开工前必读

1. `WORKFLOW.md`
2. `docs/prompts/公共项目提示词.md`
3. `docs/prompts/agents/决策提示词.md`
4. `docs/tasks/TASK-0117-decision-研究中心五项拓展.md`
5. `docs/reviews/TASK-0117-review.md`

---

## 任务背景

扩展研究中心能力至 5 个新方向，全部无人值守自动运行，异常时飞书报警：
1. **产业链价差套利自动发现** — 黑色/有色/油脂链 Z-score 超阈值时自动生成套利意图
2. **策略失效预警** — 30 日滚动 Sharpe 下滑 > 30% 连续 5 日 → P1 报警
3. **盘前资讯过滤打分** — deepcoder 对研报资讯打标，高分推送飞书
4. **参数退化自动再调优** — 每周 Optuna 重跑，差异超 15% 通知 Jay.S
5. **跨品种相关性漂移** — 35 品种相关矩阵偏离历史 > 2σ → P2 报警

---

## 白名单文件（6 个）

**Token**: `tok-f8d27abe-32ad-4b21-beae-fe03e6596ba7`

| 文件 | 操作 | 说明 |
|------|------|------|
| `services/decision/src/research/spread_monitor.py` | **新建** | 产业链价差监控 |
| `services/decision/src/research/news_scorer.py` | **新建** | 盘前资讯打分 |
| `services/decision/src/research/correlation_monitor.py` | **新建** | 跨品种相关性漂移 |
| `services/decision/src/reporting/daily.py` | **修改** | 新增策略失效预警 |
| `services/decision/src/api/routes/optimizer.py` | **修改** | 新增参数退化再调优 |
| `services/decision/tests/test_research_extensions.py` | **新建** | 5 模块测试 |

---

## 架构事实（沿用 TASK-0112 确认口径）

### 数据拉取规则
- 跨品种 K 线：`GET {DATA_API_URL}/api/v1/bars?symbol={symbol}&interval=1d`
- 股票日线：`GET {DATA_API_URL}/api/v1/stocks/bars`
- 研报：`GET {DATA_API_URL}/api/v1/researcher/report/latest`
- **不得**直接读取其他数据 API

### 飞书报警颜色标准
| 类型 | template | 场景 |
|------|---------|------|
| 套利资讯（模块1） | `blue` 📈 | 价差超阈值，自动生成意图 |
| 策略失效（模块2） | `orange` ⚠️ P1 | Sharpe 下滑触发 |
| 资讯推送（模块3） | `blue` 📈 | 高分资讯推送 |
| 参数退化（模块4） | `turquoise` 📣 | 差异 > 15% 通知 |
| 相关性漂移（模块5） | `yellow` 🔔 P2 | 偏离 > 2σ |

---

## 详细实现规格

### 模块 1：`spread_monitor.py` — 产业链价差监控（新建）

```python
class SpreadMonitor:
    """
    监控期货产业链内的价差 Z-score。
    Z-score > 2σ → deepcoder 自动生成套利策略意图 → `pipeline.full_pipeline()`
    """
    
    CHAINS = {
        "黑色链": ["rb", "hc", "i", "j", "jm"],   # 螺纹钢-热轧-铁矿-焦炭-焦煤
        "有色链": ["cu", "al", "zn"],               # 铜-铝-锌
        "油脂链": ["p", "y", "a"],                  # 棕榈-豆油-豆粕
    }
    
    def monitor_all(self) -> list[dict]:
        """拉取各链所有品种日K线，计算跨品种价差，返回超阈值触发列表"""
        ...
    
    def _calc_zscore(self, spread_series: pd.Series, window: int = 60) -> float:
        """滚动 60 日均值/标准差计算 Z-score"""
        ...
    
    def _trigger_pipeline(self, chain_name: str, pair: tuple, zscore: float) -> None:
        """
        构造套利意图 → 调 pipeline.full_pipeline()：
        意图格式："监测到 {chain_name} {pair[0]}-{pair[1]} 价差偏离 {zscore:.1f}σ，请生成套利策略"
        完成后飞书 blue 推送结果摘要
        """
        ...
```

**约束**：
- Z-score 窗口：60 个交易日
- 触发阈值：绝对值 > 2.0
- 价差计算用收盘价比值（非价差绝对值，处理不同单位问题）
- 每对品种每日最多触发一次（防止重复调用 pipeline）
- pipeline 调用失败时只记录 WARNING，不重试，不影响其他监控

---

### 模块 2：`daily.py` — 新增策略失效预警（修改）

在现有 `daily.py` 中新增：

```python
def check_strategy_health(self, strategies: list[dict]) -> list[dict]:
    """
    对每个已上线策略计算 30 日滚动 Sharpe：
    1. 拉取策略对应品种最近 30 个交易日的收益序列
    2. 计算 Sharpe = mean(returns) / std(returns) * sqrt(252)
    3. 与历史 Sharpe（策略上线时基准值）对比
    4. Sharpe 下滑 > 30% 且持续天数 >= 5 → 飞书 P1 报警（orange ⚠️）+ flag 策略状态为 degraded
    5. 报警内容含：策略名、品种、当前Sharpe、基准Sharpe、连续天数
    6. 不自动更新参数，需人工确认
    
    返回失效策略列表（空 list = 无失效）
    """
    
def _count_consecutive_degraded_days(self, strategy_id: str, 
                                      current_sharpe: float,
                                      baseline_sharpe: float) -> int:
    """持久化跟踪连续恶化天数（用简单 JSON 文件记录）"""
    ...
```

**约束**：
- 每日收盘后（或手动触发）运行
- 不修改任何已有函数签名，只新增方法
- 基准 Sharpe 通过策略元数据读取（若无则跳过该策略）

---

### 模块 3：`news_scorer.py` — 盘前资讯打分（新建）

```python
class NewsScorer:
    """
    读取 qwen3 研报 → 调 deepcoder 对每条资讯打标：
    - 影响品种列表（从 35 品种中圈定）
    - 紧急程度评分（0-10）
    已持有品种相关资讯若评分 > 7 → 飞书 blue 推送
    """
    
    SCORE_THRESHOLD = 7         # 推送阈值
    OLLAMA_MODEL = "deepcoder:14b"
    OLLAMA_URL = "http://192.168.31.142:11434"
    
    def score_report(self, report: dict, held_symbols: list[str]) -> list[dict]:
        """
        report: researcher/report/latest 返回结构
        held_symbols: 当前持有品种列表
        返回: [{"title": ..., "symbols": [...], "score": 8, "pushed": True}, ...]
        """
    
    def _build_scoring_prompt(self, news_item: str) -> str:
        """要求 deepcoder 输出 JSON: {"symbols": [...], "urgency": 0-10, "reason": "..."}"""
    
    def _push_to_feishu(self, news_item: dict) -> None:
        """使用 DecisionFeishuNotifier 发 blue 📈 消息"""
```

**约束**：
- 每条资讯独立调 deepcoder（不批量 prompt）
- deepcoder 超时（10s）时跳过该条，记录 WARNING
- 每条资讯输出 JSON 格式，解析失败时跳过
- 影响品种须在 35 品种白名单中，不接受幻觉品种

---

### 模块 4：`optimizer.py` — 新增参数退化再调优（修改）

在现有 `optimizer.py` 基础上新增：

```python
def weekly_redoplimize(self, strategy_id: str, symbol: str, 
                       current_params: dict) -> dict:
    """
    每周一夜间运行：
    1. 拉取最近 30 日数据，重跑 Optuna（n_trials=50，轻量快速）
    2. 计算新最优参数与 current_params 的差异率
       差异率 = max(|new_v - old_v| / |old_v|) across all params
    3. 差异 < 5% → 维持，仅记录日志
    4. 差异 5%-15% → 记录，暂不推送
    5. 差异 > 15% → 飞书 turquoise 📣 推送，附新旧参数对比
    6. 不自动部署，需 Jay.S 确认
    
    返回 {"strategy_id": ..., "action": "maintain|notify", "new_params": ..., "diff_rate": ...}
    """

def schedule_weekly(self) -> None:
    """注册到调度器：每周一 00:30 运行 weekly_reoptimize for all strategies"""
```

**约束**：
- 不修改现有 `optimize()` / 其他函数签名
- Optuna 使用 SQLite journal 防重跑（study_name = `{strategy_id}-weekly`）
- 飞书消息含：策略名、品种、差异率、新旧参数对比表

---

### 模块 5：`correlation_monitor.py` — 跨品种相关性漂移（新建）

```python
class CorrelationMonitor:
    """
    每日计算 35 品种相关矩阵与历史均值偏差。
    某对品种相关性偏离历史 > 2σ → 飞书 P2 yellow 报警。
    """
    
    SYMBOLS = [  # 35 品种
        "rb","hc","i","j","jm","cu","al","zn","ni","ss",
        "au","ag","sc","fu","bu","ru","sp","ap","cf","sr",
        "ma","ta","eg","pp","l","v","eb","pg","lh","p",
        "y","a","c","cs","m",
    ]
    
    HISTORY_WINDOW = 60    # 历史均值窗口（交易日）
    RECENT_WINDOW = 5      # 近期观察窗口（交易日）
    SIGMA_THRESHOLD = 2.0  # 偏离阈值
    
    def monitor(self) -> list[dict]:
        """
        1. 拉取 60+5 日的日 K 线（全 35 品种）
        2. 计算近 60 日相关矩阵均值 μ 和标准差 σ
        3. 计算近 5 日相关矩阵
        4. 找出偏离 > 2σ 的品种对
        5. 飞书 P2 推送（合并到一条消息，列出所有异常对）
        6. 返回异常对列表
        """
    
    def _calculate_correlation_matrix(self, returns: pd.DataFrame) -> pd.DataFrame:
        """计算滚动收益率相关矩阵"""
        ...
```

**约束**：
- 只关注上三角矩阵（避免重复）
- 35 品种全量计算共 595 个品种对
- 飞书消息合并（一次推送所有异常对，不逐对单独推送）
- 拉取 K 线失败时降级：用最近缓存的矩阵或跳过当日

---

### `test_research_extensions.py` — 5 模块测试（新建）

```python
class TestSpreadMonitor:
    def test_zscore_above_threshold_triggers_pipeline(self): ...
    def test_zscore_below_threshold_no_trigger(self): ...
    def test_pipeline_failure_doesnt_break_monitor(self): ...

class TestStrategyHealthCheck:
    def test_sharpe_drop_30pct_5days_fires_alert(self): ...
    def test_sharpe_drop_below_30pct_no_alert(self): ...
    def test_consecutive_days_reset_on_recovery(self): ...

class TestNewsScorer:
    def test_high_score_held_symbol_pushes_feishu(self): ...
    def test_low_score_no_push(self): ...
    def test_invalid_symbol_in_response_filtered(self): ...

class TestWeeklyReoptimize:
    def test_diff_above_15pct_sends_notification(self): ...
    def test_diff_below_5pct_no_notification(self): ...

class TestCorrelationMonitor:
    def test_correlation_shift_detected(self): ...
    def test_no_alert_within_normal_range(self): ...
```

所有测试 mock 外部调用（httpx、feishu、data API），不需真实连接。

---

## 质量标准

- [ ] `pytest services/decision/tests/test_research_extensions.py -v` 全通过
- [ ] `get_errors()` 对 6 个文件返回 0 错误
- [ ] 所有监控模块运行失败不影响主业务流程（异常捕获静默）
- [ ] 飞书颜色严格遵守统一标准（不得自定义颜色）
- [ ] 参数退化调优不自动部署，只通知

## 完工后操作

1. 运行 `pytest services/decision/tests/test_research_extensions.py -v` 截图
2. 向 Atlas 汇报，等待统一验收
3. **不得**独立 git commit（Atlas 统一收口）
