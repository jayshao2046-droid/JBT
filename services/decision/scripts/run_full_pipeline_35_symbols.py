#!/usr/bin/env python3
"""35 品种 LLM 策略自动化生产主控脚本 — TASK-0127

完整闭环流程：
1. 生成策略矩阵（7-10 个策略/品种）
2. 逐个调优（Optuna IS/OOS）
3. 本地回测（Mini 数据）
4. TqSdk 回测（Studio backtest API）
5. 评分分桶
6. 证据留存
7. 飞书通知

执行顺序：
- 35 个品种串行执行
- 每个品种内策略串行执行
- 每个策略完成后立即飞书通知

用法：
    cd /Users/jayshao/JBT/services/decision
    source ../../.venv/bin/activate
    python scripts/run_full_pipeline_35_symbols.py \\
        --data-url http://192.168.31.76:8105 \\
        --backtest-url http://192.168.31.142:8103 \\
        --ollama-url http://192.168.31.142:11434 \\
        --feishu-webhook https://open.feishu.cn/open-apis/bot/v2/hook/YOUR_TOKEN \\
        --start 2022-01-01 \\
        --end 2024-12-31 \\
        --n-trials 100
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# 添加 src 到路径
_BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_BASE))

# 加载环境变量（必须在 import src 模块之前）
from dotenv import load_dotenv
load_dotenv(_BASE / ".env")

from src.research.tqsdk_backtest_client import TqSdkBacktestClient
from src.research.evidence_manager import EvidenceManager
from src.research.feishu_strategy_notifier import FeishuStrategyNotifier
from src.research.contract_resolver import ContractResolver
from src.research.yaml_signal_executor import YAMLSignalExecutor
from src.research.symbol_profiler import SymbolProfiler
from src.research.code_generator import CodeGenerator
from src.research.strategy_param_optimizer import StrategyParamOptimizer
from src.research.strategy_evaluator import StrategyEvaluator
from src.llm.openai_client import OpenAICompatibleClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("pipeline_35")

# 35 个品种（按批次分组）
SYMBOLS_35 = [
    # 批次 1：黑色系
    "rb", "hc", "i", "j", "jm",
    # 批次 2：有色金属
    "cu", "al", "zn", "ni", "ss",
    # 批次 3：贵金属
    "au", "ag",
    # 批次 4：能化
    "sc", "fu", "bu", "ru", "sp", "eb",
    # 批次 5：农产品 CZCE
    "ap", "cf", "sr", "ma", "ta", "eg",
    # 批次 6：农产品 DCE-1
    "pp", "l", "v", "pg", "lh", "p", "y",
    # 批次 7：农产品 DCE-2
    "a", "c", "cs", "m",
]

# 策略矩阵模板（每个品种生成 7 个策略）
STRATEGY_TEMPLATES = [
    {
        "name_suffix": "trend_60m_v1",
        "category": "trend_following",
        "timeframe": 60,
        "factors": ["EMA", "ADX", "ATR"],
        "description": "60分钟EMA交叉+ADX趋势确认+ATR波动率过滤的低频趋势跟踪策略",
    },
    {
        "name_suffix": "trend_15m_v1",
        "category": "trend_following",
        "timeframe": 15,
        "factors": ["MACD", "ADX", "ATR"],
        "description": "15分钟MACD动量+ADX趋势过滤+ATR风控的中频趋势跟踪策略",
    },
    {
        "name_suffix": "breakout_30m_v1",
        "category": "breakout",
        "timeframe": 30,
        "factors": ["Bollinger", "VolumeRatio", "ATR"],
        "description": "30分钟布林带收窄后放量突破的中频突破策略",
    },
    {
        "name_suffix": "mean_reversion_15m_v1",
        "category": "mean_reversion",
        "timeframe": 15,
        "factors": ["Bollinger", "RSI", "ATR"],
        "description": "15分钟布林带+RSI超买超卖的中频均值回归策略",
    },
    {
        "name_suffix": "intraday_momentum_5m_v1",
        "category": "intraday_momentum",
        "timeframe": 5,
        "factors": ["ATR", "RSI", "VolumeRatio"],
        "description": "5分钟ATR波动脉冲+RSI动量+成交量确认的日内动量策略",
    },
    {
        "name_suffix": "intraday_oscillation_5m_v1",
        "category": "intraday_oscillation",
        "timeframe": 5,
        "factors": ["KDJ", "Bollinger", "ATR"],
        "description": "5分钟KDJ+布林带震荡区间交易的日内震荡策略",
    },
    {
        "name_suffix": "multi_factor_30m_v1",
        "category": "multi_factor",
        "timeframe": 30,
        "factors": ["MACD", "CCI", "ATR", "VolumeRatio"],
        "description": "30分钟MACD+CCI+ATR+成交量四因子复合的多因子策略",
    },
]

PROGRESS_FILE = _BASE / "runtime" / "pipeline_progress.json"


class PipelineProgress:
    """流水线进度追踪"""

    def __init__(self, progress_file: Path):
        self.progress_file = progress_file
        self.progress_file.parent.mkdir(parents=True, exist_ok=True)
        self.data = self._load()

    def _load(self) -> dict:
        if self.progress_file.exists():
            with open(self.progress_file, "r") as f:
                return json.load(f)
        return {
            "current_symbol": None,
            "completed_symbols": [],
            "current_strategy_index": 0,
            "total_strategies": 0,
            "start_time": None,
            "last_update": None,
        }

    def save(self):
        self.data["last_update"] = datetime.now().isoformat()
        with open(self.progress_file, "w") as f:
            json.dump(self.data, f, indent=2)

    def start_symbol(self, symbol: str, total_strategies: int):
        self.data["current_symbol"] = symbol
        self.data["current_strategy_index"] = 0
        self.data["total_strategies"] = total_strategies
        if not self.data["start_time"]:
            self.data["start_time"] = datetime.now().isoformat()
        self.save()

    def complete_strategy(self):
        self.data["current_strategy_index"] += 1
        self.save()

    def complete_symbol(self, symbol: str):
        if symbol not in self.data["completed_symbols"]:
            self.data["completed_symbols"].append(symbol)
        self.data["current_symbol"] = None
        self.save()


async def process_one_strategy(
    symbol: str,
    template: dict,
    yaml_path: Path,
    executor: YAMLSignalExecutor,
    optimizer: StrategyParamOptimizer,
    evaluator: StrategyEvaluator,
    tqsdk_client: TqSdkBacktestClient,
    evidence_mgr: EvidenceManager,
    feishu_notifier: FeishuStrategyNotifier,
    start_date: str,
    end_date: str,
    idx: int,
    total: int,
) -> dict[str, Any]:
    """处理单个策略的完整流程"""

    strategy_name = yaml_path.stem
    logger.info(f"\n{'═' * 60}")
    logger.info(f"[{idx}/{total}] 开始处理策略: {strategy_name}")
    logger.info(f"{'═' * 60}")

    result = {
        "strategy_name": strategy_name,
        "symbol": symbol,
        "category": template["category"],
        "status": "pending",
    }

    try:
        # 读取策略 YAML
        import yaml
        with open(yaml_path, "r", encoding="utf-8") as f:
            strategy = yaml.safe_load(f)

        # 1. 调优
        logger.info(f"  [1/5] 开始调优...")
        opt_result = await optimizer.optimize(strategy, start_date, end_date)
        result["optimization"] = opt_result
        evidence_mgr.save_optimization_report(symbol, strategy_name, opt_result)

        # 2. 本地回测
        logger.info(f"  [2/5] 本地回测...")
        local_result = await executor.execute(strategy, start_date, end_date)
        result["local_backtest"] = local_result.to_dict()
        evidence_mgr.save_local_backtest_report(symbol, strategy_name, local_result.to_dict())

        # 3. TqSdk 回测
        logger.info(f"  [3/5] TqSdk 回测...")
        task_id = await tqsdk_client.submit_backtest(yaml_path, start_date, end_date)
        tqsdk_result = await tqsdk_client.poll_result(task_id)
        result["tqsdk_backtest"] = tqsdk_result
        evidence_mgr.save_tqsdk_backtest_report(symbol, strategy_name, tqsdk_result)

        # 4. 评分
        logger.info(f"  [4/5] 策略评分...")
        eval_result = await evaluator.evaluate_strategy(str(yaml_path), start_date, end_date)
        result["evaluation"] = eval_result
        evidence_mgr.save_evaluator_report(symbol, strategy_name, eval_result)

        # 5. 分桶归档
        logger.info(f"  [5/5] 分桶归档...")
        final_score = eval_result.get("final_score", 0)
        grade = eval_result.get("grade", "D")
        is_fused = grade == "BLOCKED"

        storage_path = evidence_mgr.move_to_bucket(
            yaml_path, symbol, strategy_name, final_score, is_fused
        )
        evidence_mgr.copy_reports_to_bucket(symbol, strategy_name, final_score, is_fused)

        result["storage_path"] = str(storage_path)
        result["final_score"] = final_score
        result["grade"] = grade
        result["status"] = "completed"

        # 6. 飞书通知
        logger.info(f"  [6/6] 发送飞书通知...")
        await feishu_notifier.notify_strategy_completed(
            symbol=symbol,
            strategy_name=strategy_name,
            category=template["category"],
            factors=template["factors"],
            params=strategy,
            local_result=local_result.to_dict(),
            tqsdk_result=tqsdk_result,
            final_score=final_score,
            grade=grade,
            optimization_trials=opt_result.get("n_trials", 0),
            storage_path=str(storage_path),
        )

        logger.info(f"✅ 策略完成: {strategy_name} (得分: {final_score}, 等级: {grade})")

    except Exception as e:
        logger.exception(f"❌ 策略处理失败: {strategy_name}")
        result["status"] = "failed"
        result["error"] = str(e)

    return result


async def generate_strategies_for_symbol(
    symbol: str,
    output_dir: Path,
    data_url: str,
    ollama_url: str,
    evidence_mgr: EvidenceManager,
) -> list[Path]:
    """为单个品种生成策略矩阵

    Args:
        symbol: 品种代码
        output_dir: 输出目录
        data_url: Mini data API 地址
        ollama_url: Ollama API 地址
        evidence_mgr: 证据管理器

    Returns:
        生成的 YAML 文件路径列表
    """
    logger.info(f"  开始生成策略矩阵...")

    # 初始化组件
    client = OpenAICompatibleClient(component=f"pipeline_{symbol}")
    profiler = SymbolProfiler(data_service_url=data_url)
    generator = CodeGenerator(
        online_client=client,
        model="deepseek-v3.2",  # Coder 角色，降级链: deepseek-v3 → qwen3.6-plus
        output_dir=str(output_dir),
    )

    # CZCE 品种列表
    CZCE_COMMODITIES = {"cf", "sr", "ma", "ta", "ap", "cy", "fg", "oi", "rm", "rs", "sf", "sm", "wh", "zc", "eg"}

    # 确定交易所前缀
    exchange_prefix = "CZCE" if symbol.lower() in CZCE_COMMODITIES else "DCE"
    symbol_with_exchange = f"{exchange_prefix}.{symbol.upper() if exchange_prefix == 'CZCE' else symbol}"

    # 1. 品种特征分析
    try:
        features = await profiler.calculate_features(symbol=symbol_with_exchange)
        features_desc = f"品种: {symbol}, 波动率: {features.volatility_weighted}, 趋势强度: {features.trend_strength_weighted}"
    except Exception as e:
        logger.warning(f"  品种特征分析失败: {e}，使用默认特征")
        features_desc = f"品种: {symbol}"

    # 2. 逐个生成策略
    yaml_files = []
    for template in STRATEGY_TEMPLATES:
        strategy_name = f"{symbol}_{template['name_suffix']}"
        yaml_path = output_dir / f"{strategy_name}.yaml"

        # 如果文件已存在，跳过生成
        if yaml_path.exists():
            logger.info(f"  ✓ 策略已存在: {strategy_name}")
            yaml_files.append(yaml_path)
            continue

        try:
            # 构建设计 prompt
            design_prompt = f"""为 {symbol} 品种设计一个 {template['category']} 策略。
品种特征: {features_desc}
时间周期: {template['timeframe']} 分钟
核心因子: {', '.join(template['factors'])}
策略描述: {template['description']}

输出 JSON 格式的策略设计，包含：
- strategy_name: {strategy_name}
- logic_description: 策略逻辑描述
- entry_logic: 做多入场条件
- exit_logic: 做多出场条件
- short_entry_logic: 做空入场条件
- short_exit_logic: 做空出场条件
"""

            # 调用 LLM 设计策略
            messages = [
                {"role": "system", "content": "你是策略设计专家，输出纯 JSON。"},
                {"role": "user", "content": design_prompt},
            ]

            response = await client.chat("gpt-5.4", messages, timeout=120.0)
            if "error" in response:
                logger.error(f"  ✗ 设计失败: {response['error']}")
                continue

            # 解析设计结果
            import json
            import re
            content = response.get("content", "")
            content = content.replace("```json", "").replace("```", "").strip()
            match = re.search(r'\{.*\}', content, re.DOTALL)
            if match:
                design = json.loads(match.group(0))
            else:
                design = json.loads(content)

            design["strategy_name"] = strategy_name

            # 生成 YAML
            yaml_path = await generator.generate_yaml_strategy(
                strategy_design=design,
                symbol=symbol_with_exchange,
                timeframe=template["timeframe"],
            )

            if yaml_path:
                logger.info(f"  ✓ 策略已生成: {strategy_name}")
                yaml_files.append(Path(yaml_path))

                # 保存 generation_report
                generation_report = {
                    "strategy_name": strategy_name,
                    "symbol": symbol,
                    "category": template["category"],
                    "timeframe": template["timeframe"],
                    "factors": template["factors"],
                    "design_prompt": design_prompt,
                    "design_response": design,
                    "model": "gpt-5.4",
                    "generated_at": datetime.now().isoformat(),
                    "yaml_path": str(yaml_path),
                }
                evidence_mgr.save_generation_report(symbol, strategy_name, generation_report)

        except Exception as e:
            logger.error(f"  ✗ 生成失败 ({strategy_name}): {e}")

    # 关闭客户端
    try:
        await client._client.aclose()
    except Exception:
        pass

    logger.info(f"  策略生成完成: {len(yaml_files)}/{len(STRATEGY_TEMPLATES)}")
    return yaml_files


async def process_one_symbol(
    symbol: str,
    args: argparse.Namespace,
    progress: PipelineProgress,
) -> dict[str, Any]:
    """处理单个品种的完整流程"""

    logger.info(f"\n{'━' * 80}")
    logger.info(f"开始处理品种: {symbol}")
    logger.info(f"{'━' * 80}")

    # 初始化组件
    executor = YAMLSignalExecutor(args.data_url, args.ollama_url)
    optimizer = StrategyParamOptimizer(executor, n_trials=args.n_trials)
    evaluator = StrategyEvaluator(args.data_url, args.ollama_url)
    tqsdk_client = TqSdkBacktestClient(args.backtest_url)
    evidence_mgr = EvidenceManager(_BASE / "strategies" / "llm_ranked")
    feishu_notifier = FeishuStrategyNotifier(args.feishu_webhook)

    # 策略生成目录
    output_dir = _BASE / "strategies" / "llm_generated" / symbol
    output_dir.mkdir(parents=True, exist_ok=True)

    # 生成策略矩阵
    yaml_files = await generate_strategies_for_symbol(
        symbol=symbol,
        output_dir=output_dir,
        data_url=args.data_url,
        ollama_url=args.ollama_url,
        evidence_mgr=evidence_mgr,
    )

    if not yaml_files:
        logger.warning(f"品种 {symbol} 未生成任何策略，跳过")
        return {
            "symbol": symbol,
            "total": 0,
            "completed": 0,
            "failed": 0,
            "results": [],
        }

    progress.start_symbol(symbol, len(yaml_files))

    # 逐个处理策略
    results = []
    for idx, yaml_path in enumerate(yaml_files, 1):
        template = STRATEGY_TEMPLATES[idx - 1]
        result = await process_one_strategy(
            symbol=symbol,
            template=template,
            yaml_path=yaml_path,
            executor=executor,
            optimizer=optimizer,
            evaluator=evaluator,
            tqsdk_client=tqsdk_client,
            evidence_mgr=evidence_mgr,
            feishu_notifier=feishu_notifier,
            start_date=args.start,
            end_date=args.end,
            idx=idx,
            total=len(yaml_files),
        )
        results.append(result)
        progress.complete_strategy()

    progress.complete_symbol(symbol)

    # 统计
    completed = sum(1 for r in results if r["status"] == "completed")
    failed = len(results) - completed

    logger.info(f"\n品种 {symbol} 完成: {completed}/{len(results)} 成功, {failed} 失败")

    return {
        "symbol": symbol,
        "total": len(results),
        "completed": completed,
        "failed": failed,
        "results": results,
    }


async def main():
    parser = argparse.ArgumentParser(description="35 品种 LLM 策略自动化生产主控脚本")
    parser.add_argument("--data-url", default="http://192.168.31.76:8105")
    parser.add_argument("--backtest-url", default="http://192.168.31.142:8103")
    parser.add_argument("--ollama-url", default="http://192.168.31.142:11434")
    parser.add_argument("--feishu-webhook", required=True)
    parser.add_argument("--start", default="2022-01-01")
    parser.add_argument("--end", default="2024-12-31")
    parser.add_argument("--n-trials", type=int, default=100)
    parser.add_argument("--symbols", nargs="+", help="指定品种（默认全部 35 个）")
    args = parser.parse_args()

    symbols = args.symbols or SYMBOLS_35

    logger.info("=" * 80)
    logger.info("35 品种 LLM 策略自动化生产流水线")
    logger.info("=" * 80)
    logger.info(f"品种数量: {len(symbols)}")
    logger.info(f"回测区间: {args.start} ~ {args.end}")
    logger.info(f"调优次数: {args.n_trials} trials")
    logger.info("=" * 80)

    progress = PipelineProgress(PROGRESS_FILE)

    all_results = []
    for symbol in symbols:
        if symbol in progress.data["completed_symbols"]:
            logger.info(f"⏭️  品种 {symbol} 已完成，跳过")
            continue

        result = await process_one_symbol(symbol, args, progress)
        all_results.append(result)

    # 全局汇总
    logger.info("\n" + "=" * 80)
    logger.info("全局汇总")
    logger.info("=" * 80)
    total_strategies = sum(r["total"] for r in all_results)
    total_completed = sum(r["completed"] for r in all_results)
    total_failed = sum(r["failed"] for r in all_results)

    logger.info(f"总策略数: {total_strategies}")
    logger.info(f"成功: {total_completed}")
    logger.info(f"失败: {total_failed}")
    logger.info(f"成功率: {total_completed / total_strategies * 100:.1f}%")

    logger.info("\n🎉 35 品种流水线全部完成！")


if __name__ == "__main__":
    asyncio.run(main())
