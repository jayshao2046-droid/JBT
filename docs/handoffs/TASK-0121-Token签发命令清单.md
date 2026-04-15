# TASK-0121 Token 签发命令清单

【创建时间】2026-04-16 02:10  
【任务】TASK-0121 — data 研究员 24/7 重构  
【签发人】Jay.S  
【执行 Agent】Claude-Code

---

## 签发顺序

按照项目架构师建议，共 10 个批次，45 文件。

---

## M1 批次 - Mini API 端点（2 文件）

```bash
cd /Users/jayshao/JBT

python governance/jbt_lockctl.py issue \
  --task TASK-0121-M1 \
  --agent "Claude-Code" \
  --action "实现 Mini API /api/v1/bars 端点" \
  --files services/data/src/main.py services/data/tests/test_api_bars.py \
  --ttl-minutes 30
```

**文件清单**:
- `services/data/src/main.py` (修改)
- `services/data/tests/test_api_bars.py` (新建)

---

## A1 批次 - 多进程骨架（10 文件）

```bash
python governance/jbt_lockctl.py issue \
  --task TASK-0121-A1 \
  --agent "Claude-Code" \
  --action "实现研究员多进程骨架" \
  --files \
    services/data/src/researcher/__init__.py \
    services/data/src/researcher/process_manager.py \
    services/data/src/researcher/shared_queue.py \
    services/data/src/researcher/kline_monitor.py \
    services/data/src/researcher/news_crawler.py \
    services/data/src/researcher/fundamental_crawler.py \
    services/data/src/researcher/llm_analyzer.py \
    services/data/src/researcher/report_generator.py \
    services/data/src/researcher/memory_db.py \
    services/data/tests/test_researcher_multiprocess.py \
  --ttl-minutes 60
```

**文件清单**:
- `services/data/src/researcher/__init__.py` (修改)
- `services/data/src/researcher/process_manager.py` (新建)
- `services/data/src/researcher/shared_queue.py` (新建)
- `services/data/src/researcher/kline_monitor.py` (新建)
- `services/data/src/researcher/news_crawler.py` (新建)
- `services/data/src/researcher/fundamental_crawler.py` (新建)
- `services/data/src/researcher/llm_analyzer.py` (新建)
- `services/data/src/researcher/report_generator.py` (新建)
- `services/data/src/researcher/memory_db.py` (新建)
- `services/data/tests/test_researcher_multiprocess.py` (新建)

---

## A2 批次 - K 线监控器（3 文件）

```bash
python governance/jbt_lockctl.py issue \
  --task TASK-0121-A2 \
  --agent "Claude-Code" \
  --action "实现 K 线监控器" \
  --files \
    services/data/src/researcher/kline_monitor.py \
    services/data/src/researcher/session_detector.py \
    services/data/tests/test_kline_monitor.py \
  --ttl-minutes 30
```

**文件清单**:
- `services/data/src/researcher/kline_monitor.py` (修改)
- `services/data/src/researcher/session_detector.py` (新建)
- `services/data/tests/test_kline_monitor.py` (新建)

---

## A3 批次 - 新闻爬虫（6 文件）

```bash
python governance/jbt_lockctl.py issue \
  --task TASK-0121-A3 \
  --agent "Claude-Code" \
  --action "实现新闻爬虫" \
  --files \
    services/data/src/researcher/news_crawler.py \
    services/data/src/researcher/crawler/engine.py \
    services/data/src/researcher/crawler/parsers/generic.py \
    services/data/src/researcher/crawler/parsers/futures.py \
    services/data/configs/researcher_sources.yaml \
    services/data/tests/test_news_crawler.py \
  --ttl-minutes 45
```

**文件清单**:
- `services/data/src/researcher/news_crawler.py` (修改)
- `services/data/src/researcher/crawler/engine.py` (新建)
- `services/data/src/researcher/crawler/parsers/generic.py` (新建)
- `services/data/src/researcher/crawler/parsers/futures.py` (新建)
- `services/data/configs/researcher_sources.yaml` (新建)
- `services/data/tests/test_news_crawler.py` (新建)

---

## A4 批次 - 基本面爬虫（4 文件）

```bash
python governance/jbt_lockctl.py issue \
  --task TASK-0121-A4 \
  --agent "Claude-Code" \
  --action "实现基本面爬虫" \
  --files \
    services/data/src/researcher/fundamental_crawler.py \
    services/data/src/researcher/crawler/parsers/warehouse.py \
    services/data/src/researcher/crawler/parsers/inventory.py \
    services/data/tests/test_fundamental_crawler.py \
  --ttl-minutes 30
```

**文件清单**:
- `services/data/src/researcher/fundamental_crawler.py` (修改)
- `services/data/src/researcher/crawler/parsers/warehouse.py` (新建)
- `services/data/src/researcher/crawler/parsers/inventory.py` (新建)
- `services/data/tests/test_fundamental_crawler.py` (新建)

---

## A5 批次 - LLM 分析器（4 文件）

```bash
python governance/jbt_lockctl.py issue \
  --task TASK-0121-A5 \
  --agent "Claude-Code" \
  --action "实现 LLM 分析器和连贯写作" \
  --files \
    services/data/src/researcher/llm_analyzer.py \
    services/data/src/researcher/memory_db.py \
    services/data/src/researcher/prompts.py \
    services/data/tests/test_llm_analyzer.py \
  --ttl-minutes 45
```

**文件清单**:
- `services/data/src/researcher/llm_analyzer.py` (修改)
- `services/data/src/researcher/memory_db.py` (修改)
- `services/data/src/researcher/prompts.py` (新建)
- `services/data/tests/test_llm_analyzer.py` (新建)

---

## A6 批次 - 报告生成器（5 文件）

```bash
python governance/jbt_lockctl.py issue \
  --task TASK-0121-A6 \
  --agent "Claude-Code" \
  --action "实现报告生成器和推送" \
  --files \
    services/data/src/researcher/report_generator.py \
    services/data/src/researcher/report_templates.py \
    services/data/src/researcher/feishu_sender.py \
    services/data/src/researcher/email_sender.py \
    services/data/tests/test_report_generator.py \
  --ttl-minutes 45
```

**文件清单**:
- `services/data/src/researcher/report_generator.py` (修改)
- `services/data/src/researcher/report_templates.py` (新建)
- `services/data/src/researcher/feishu_sender.py` (新建)
- `services/data/src/researcher/email_sender.py` (新建)
- `services/data/tests/test_report_generator.py` (新建)

---

## D1 批次 - 决策端对接（4 文件）

```bash
python governance/jbt_lockctl.py issue \
  --task TASK-0121-D1 \
  --agent "Claude-Code" \
  --action "实现决策端研报对接" \
  --files \
    services/decision/src/llm/researcher_loader.py \
    services/decision/src/llm/researcher_scorer.py \
    services/decision/src/llm/pipeline.py \
    services/decision/tests/test_researcher_integration.py \
  --ttl-minutes 45
```

**文件清单**:
- `services/decision/src/llm/researcher_loader.py` (新建)
- `services/decision/src/llm/researcher_scorer.py` (新建)
- `services/decision/src/llm/pipeline.py` (修改)
- `services/decision/tests/test_researcher_integration.py` (新建)

---

## D2 批次 - Dashboard 控制台（4 文件）

```bash
python governance/jbt_lockctl.py issue \
  --task TASK-0121-D2 \
  --agent "Claude-Code" \
  --action "实现 Dashboard 研究员控制台" \
  --files \
    services/dashboard/dashboard_web/app/data/researcher/page.tsx \
    services/dashboard/dashboard_web/app/data/researcher/components/source-manager.tsx \
    services/dashboard/dashboard_web/app/data/researcher/components/priority-adjuster.tsx \
    services/dashboard/dashboard_web/app/data/researcher/components/report-viewer.tsx \
  --ttl-minutes 45
```

**文件清单**:
- `services/dashboard/dashboard_web/app/data/researcher/page.tsx` (新建)
- `services/dashboard/dashboard_web/app/data/researcher/components/source-manager.tsx` (新建)
- `services/dashboard/dashboard_web/app/data/researcher/components/priority-adjuster.tsx` (新建)
- `services/dashboard/dashboard_web/app/data/researcher/components/report-viewer.tsx` (新建)

---

## C1 批次 - 对话控制（3 文件）

```bash
python governance/jbt_lockctl.py issue \
  --task TASK-0121-C1 \
  --agent "Claude-Code" \
  --action "实现 qwen3:14b 对话控制" \
  --files \
    services/data/src/researcher/chat_controller.py \
    services/data/src/researcher/config_updater.py \
    services/data/tests/test_chat_controller.py \
  --ttl-minutes 30
```

**文件清单**:
- `services/data/src/researcher/chat_controller.py` (新建)
- `services/data/src/researcher/config_updater.py` (新建)
- `services/data/tests/test_chat_controller.py` (新建)

---

## 签发统计

| 批次 | 文件数 | 时长 | 说明 |
|------|--------|------|------|
| M1 | 2 | 30 分钟 | Mini API 端点 |
| A1 | 10 | 60 分钟 | 多进程骨架 |
| A2 | 3 | 30 分钟 | K 线监控器 |
| A3 | 6 | 45 分钟 | 新闻爬虫 |
| A4 | 4 | 30 分钟 | 基本面爬虫 |
| A5 | 4 | 45 分钟 | LLM 分析器 |
| A6 | 5 | 45 分钟 | 报告生成器 |
| D1 | 4 | 45 分钟 | 决策端对接 |
| D2 | 4 | 45 分钟 | Dashboard 控制台 |
| C1 | 3 | 30 分钟 | 对话控制 |
| **总计** | **45** | **405 分钟** | **~6.75 小时** |

---

## 执行说明

1. 在终端 cd 到 `/Users/jayshao/JBT`
2. 逐个执行上述命令
3. 每次执行时输入密码
4. 记录每个批次的 Token 字符串
5. 执行完成后通知 Claude-Code 开始实施

---

**创建人**: Kiro (Claude Code)  
**日期**: 2026-04-16  
**状态**: 等待 Jay.S 签发
