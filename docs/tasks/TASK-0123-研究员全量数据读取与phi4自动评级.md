# TASK-0123 — 研究员全量数据读取与 phi4 自动评级

**创建**: 2026-04-16  
**状态**: 调研中  
**优先级**: P0  
**依赖**: TASK-0121

---

## 用户需求

### 1. 让研究员读取 Mini 全量数据生成研报
- 研究员要读**本地文件**而非 Docker 内的文件
- 确保能读到 Mini 上的 2.3GB 数据（2986 个 parquet 文件）

### 2. 每次生成研报自动触发 phi4 评级
- 研究员生成报告后自动通知 Studio phi4 进行评级
- phi4 评级结果通过飞书卡片通知

### 3. 数据分类与研报组织
用户提出的问题：
> data 上很多各种数据 qwen 会自动分类吗？还是需要我们给他进行分类，一个类别一份研报？

用户的想法：
> data 的连续采集数据一个类型一个文档连续更新，旧数据可查。爬虫采集的数据按照采集时间更新一个文件研报文件，不断更新

---

## 当前问题诊断

### 问题 1: Mini API 端点缺失
- 研究员通过 `MiniClient` 调用 `http://192.168.31.76:8105/api/v1/bars`
- **该端点不存在**（TASK-0121 已确认）
- 导致研究员无法读取 Mini 的 2.3GB 数据

### 问题 2: 网络共享不可用
- Alienware 无法通过 SMB/NFS 访问 Mini 的文件系统
- 测试 `\\192.168.31.76\jbt\data` 返回 False

### 问题 3: 数据分类不明确
- Mini 上有多种数据类型：
  - 期货分钟数据: `~/jbt/data/futures_minute/1m/` (353 MB, 262 品种)
  - 股票分钟数据: `~/jbt/data/{股票代码}/stock_minute/records.parquet` (5368 只)
  - 爬虫数据: 新闻、基本面、情绪数据
- 当前研究员生成**单一报告**，包含所有数据
- 用户希望按数据类型分类生成多份研报

### 问题 4: phi4 评级未自动触发
- 当前需要手动运行 `test_researcher_evaluation.py`
- 研究员生成报告后不会自动通知 phi4

---

## 解决方案设计

### 方案 A: 实现 Mini `/api/v1/bars` 端点（推荐）

**优点**:
- 符合 TASK-0121 架构设计
- 研究员代码无需大改
- 支持增量读取和过滤

**实现**:
1. 在 Mini `services/data/src/main.py` 添加 `/api/v1/bars` 端点
2. 读取 `~/jbt/data/futures_minute/1m/{symbol}/` 下的 parquet 文件
3. 支持参数: `symbol`, `start`, `end`, `limit`

**工作量**: 2 文件，约 1 小时

---

### 方案 B: Alienware 直接读取 Mini 文件（需要网络共享）

**优点**:
- 无需 API，直接读取文件
- 性能更好（无 HTTP 开销）

**缺点**:
- 需要配置 Mini 的 SMB/NFS 共享
- Alienware 需要挂载网络驱动器
- 跨平台兼容性问题（Mac → Windows）

**实现**:
1. Mini 配置 SMB 共享: `~/jbt/data` → `\\192.168.31.76\jbt\data`
2. Alienware 挂载网络驱动器: `net use Z: \\192.168.31.76\jbt\data`
3. 修改研究员代码，直接读取 `Z:\futures_minute\1m\`

**工作量**: 配置 + 2 文件，约 2 小时

---

### 方案 C: rsync 定期同步数据到 Alienware（不推荐）

**优点**:
- Alienware 本地读取，速度快

**缺点**:
- 数据延迟（同步间隔）
- 占用 Alienware 存储空间（2.3GB+）
- 需要定时任务维护

**工作量**: 配置 + 脚本，约 1 小时

---

## 数据分类与研报组织方案

### 当前架构（单一报告）
```
研究员 → 生成单一报告 (RPT-20260416-16:00-002)
  ├── futures_summary (期货汇总)
  ├── stocks_summary (股票汇总)
  ├── crawler_stats (爬虫统计)
  └── change_highlights (变化亮点)
```

### 方案 1: 按数据类型分层报告（推荐）

**结构**:
```
研究员 → 生成多份报告
  ├── 连续数据报告 (每小时更新)
  │   ├── futures_report.json (期货 K 线分析)
  │   ├── stocks_report.json (股票 K 线分析)
  │   └── market_overview.json (市场概览)
  │
  ├── 爬虫数据报告 (按采集时间更新)
  │   ├── news_report_{timestamp}.json (新闻汇总)
  │   ├── fundamental_report_{timestamp}.json (基本面数据)
  │   └── sentiment_report_{timestamp}.json (情绪分析)
  │
  └── 综合报告 (定时生成)
      └── comprehensive_report_{timestamp}.json (整合所有数据)
```

**优点**:
- 数据分类清晰
- 连续数据可持续更新（旧数据可查）
- 爬虫数据按时间归档
- phi4 可针对不同类型报告进行专项评级

**实现**:
1. 修改 `report_generator.py`，支持多种报告类型
2. 每种报告类型有独立的模板和生成逻辑
3. 连续数据报告使用**增量更新**模式（append）
4. 爬虫数据报告使用**时间戳归档**模式（snapshot）

---

### 方案 2: 单一报告 + 历史版本（当前方案）

**结构**:
```
研究员 → 生成单一报告 (每小时一份)
  └── RPT-20260416-{HH:00}-{version}.json
      ├── futures_summary
      ├── stocks_summary
      ├── crawler_stats
      └── change_highlights
```

**优点**:
- 实现简单
- 历史版本通过文件名区分

**缺点**:
- 数据混杂，难以针对性分析
- 旧数据查询不便（需要遍历所有历史文件）
- phi4 评级粒度粗（只能整体评分）

---

## phi4 自动评级集成

### 当前流程
```
研究员生成报告 → 落盘到 D:\researcher_reports
                ↓
            (手动运行测试脚本)
                ↓
Studio phi4 读取报告 → 评级 → 飞书通知
```

### 目标流程
```
研究员生成报告 → 落盘到 D:\researcher_reports
                ↓
            触发 webhook/API 调用
                ↓
Studio phi4 自动读取 → 评级 → 飞书通知
```

### 实现方案

#### 方案 1: 研究员主动推送（推荐）
```python
# 在 report_generator.py 中
def _save_report(self, report):
    # 1. 保存到本地
    self._save_to_disk(report)
    
    # 2. 触发 phi4 评级
    self._trigger_phi4_evaluation(report)

def _trigger_phi4_evaluation(self, report):
    """触发 Studio phi4 评级"""
    try:
        studio_url = "http://192.168.31.142:8104/api/v1/evaluate_report"
        resp = httpx.post(studio_url, json={
            "report_id": report["report_id"],
            "report_path": f"http://192.168.31.224:8199/reports/latest"
        }, timeout=5.0)
        logger.info(f"Triggered phi4 evaluation: {resp.status_code}")
    except Exception as e:
        logger.warning(f"Failed to trigger phi4 evaluation: {e}")
```

**优点**:
- 实时触发，无延迟
- 研究员控制评级时机

**缺点**:
- 研究员依赖 Studio 服务可用性

---

#### 方案 2: Studio 定时轮询
```python
# 在 Studio decision 服务中添加定时任务
@scheduler.scheduled_job('interval', minutes=5)
async def auto_evaluate_reports():
    """每 5 分钟检查是否有新报告"""
    latest_report = await researcher_loader.get_latest_report()
    
    if latest_report and not is_evaluated(latest_report["report_id"]):
        await pipeline.evaluate_researcher_report()
```

**优点**:
- 研究员无需关心 Studio 状态
- 解耦合

**缺点**:
- 有延迟（最多 5 分钟）
- 需要维护已评级报告列表

---

#### 方案 3: 文件系统监听（不推荐）
使用 `watchdog` 监听 `D:\researcher_reports` 目录变化

**缺点**:
- 跨机器监听复杂
- 需要额外服务

---

## 推荐实施路径

### 阶段 1: 快速验证（1-2 小时）
1. ✅ 实现 Mini `/api/v1/bars` 端点
2. ✅ 手动触发研究员生成全量数据报告
3. ✅ 验证 phi4 评级流程

### 阶段 2: 自动化集成（2-3 小时）
1. 研究员生成报告后自动触发 phi4 评级（方案 1）
2. 添加评级失败重试机制
3. 飞书通知优化（区分报告类型）

### 阶段 3: 数据分类重构（4-6 小时）
1. 实现分层报告架构（方案 1）
2. 连续数据报告增量更新
3. 爬虫数据报告时间戳归档
4. phi4 针对不同报告类型专项评级

### 阶段 4: TASK-0121 完整实现（20-30 小时）
1. 多进程架构（5 进程）
2. 24/7 内外盘联动
3. 爬虫采集（新闻 + 基本面）
4. LLM 连贯写作

---

## 风险评估

### 技术风险
1. **Mini API 性能**: 2986 个 parquet 文件，全量读取可能较慢
   - 缓解: 实现增量读取 + 缓存
   
2. **qwen3:14b 推理速度**: 全量数据分析可能超时
   - 缓解: 分批处理 + 优先级队列

3. **网络稳定性**: Alienware ↔ Mini ↔ Studio 三方通信
   - 缓解: 超时重试 + 降级处理

### 业务风险
1. **数据质量**: Mini 数据可能不完整或有错误
   - 缓解: 数据完整性检查 + 异常告警

2. **报告质量**: 全量数据可能导致报告过于冗长
   - 缓解: 智能摘要 + 重点突出

---

## 下一步行动

### 立即执行（今天）
1. [ ] 实现 Mini `/api/v1/bars` 端点
2. [ ] 手动触发研究员生成全量数据报告
3. [ ] 验证 phi4 评级流程

### 短期（本周）
1. [ ] 研究员自动触发 phi4 评级
2. [ ] 数据分类方案确认
3. [ ] 分层报告架构设计

### 中期（下周）
1. [ ] 实现分层报告
2. [ ] TASK-0121 批次 M1 + A1 实施

---

**签名**: Kiro (Claude Code)  
**日期**: 2026-04-16  
**状态**: 调研完成，待用户确认方案
