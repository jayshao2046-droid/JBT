# HANDOFF-U0-20260419-010 data端schema冲突根治与CFTC采集器升级

【日期】2026-04-19  
【类型】U0 事后交接  
【状态】✅ 已收口  
【设备】Mini (192.168.31.76)，容器 JBT-DATA-8105

## 问题背景

Mini JBT-DATA-8105 健康报告 17/21 红，情绪/RSS/新闻API/天气采集失败。  
根因：旧 parquet 文件 payload 字段为 string 类型，新采集器写 struct，PyArrow merge 报错。  
附加问题：CFTC 采集器使用已废弃的 akshare API，全量 fallback 到 mock。

## 本轮修复内容

1. **删除 11 个旧 schema parquet 文件**（两轮扫描：weather/sentiment/news_api/news_rss + options/forex/shipping/macro_global/position_daily/cftc/volatility_index）
2. **部署修复后的 health_check.py**（position_daily 路径 `"position"` → `"position_daily"`，已在上轮 007 完成，本轮验证通过）
3. **升级 cftc_collector.py**：从废弃的 `macro_usa_cftc_nc_report` 迁移到 `macro_usa_cftc_merchant_goods_holding`
4. **代理开启后补采**：shipping 120条（含 scfi/ccfi）+ CFTC 10条 + RSS 139条

## 验收证据

| 数据类型 | 行数 | schema |
|---------|------|--------|
| weather | 105 | struct ✅ |
| sentiment | 424 | struct ✅ |
| news_api | 1544 | struct ✅ |
| news_rss | 100 | struct ✅ |
| macro_global | 497 | struct ✅ |
| shipping | 120 | ✅ |
| cftc | 10 | ✅ |

全量采集：11/14 成功（3个失败为需参数的定向 pipeline，非采集器问题）。

## 遗留注意事项

1. **容器重启后 cftc_collector.py 会被旧镜像覆盖**：
   ```bash
   rsync -avz /Users/jayshao/JBT/services/data/src/collectors/cftc_collector.py \
     jaybot@192.168.31.76:~/JBT/services/data/src/collectors/cftc_collector.py
   ```
   然后重建镜像，或在 Dockerfile 中更新依赖。

2. scfi/ccfi 无代理时 403 为已知限制（investing.com 封锁直连），非 bug。

3. CFTC 新 API 品种列表有变化（删除了 copper/wheat/sp500/nasdaq，新增 cotton/sugar），  
   与旧版本不完全一致，下游使用方注意字段对齐。

## 关联文档

- 任务建档：`docs/tasks/TASK-U0-20260419-010-data端schema冲突根治与CFTC采集器升级.md`
- 审计报告：`docs/reviews/REVIEW-U0-20260419-010-事后审计.md`
- 锁控记录：`docs/locks/lock-U0-20260419-010.md`
