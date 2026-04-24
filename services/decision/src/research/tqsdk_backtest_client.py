"""TqSdk 回测客户端 — TASK-0127

通过 decision 内部 formal runner 执行 TqSdk 在线回测，不再依赖 Studio backtest HTTP。

功能：
1. 提交内部 TqSdk formal backtest 任务
2. 等待并返回 formal_report_v1 结果
3. YAML 预处理与验证（TqSdk 兼容性检查）
4. 主力合约代码转换
"""
from __future__ import annotations

import asyncio
import logging
import re
from pathlib import Path
from typing import Any, Optional

import yaml

from src.backtest.runner import (
    BacktestExecutionError,
    BacktestJobInput,
    OnlineBacktestRunner,
)
from src.core.settings import get_settings

logger = logging.getLogger(__name__)


class TqSdkBacktestError(Exception):
    """TqSdk 回测异常"""
    pass


class TqSdkBacktestClient:
    """TqSdk 回测客户端（通过 decision 内部 runner）"""

    # 夜盘品种列表
    NIGHT_TRADING_COMMODITIES = {
        # 黑色系
        "rb", "hc", "i", "j", "jm",
        # 有色金属
        "cu", "al", "zn", "ni", "ss",
        # 贵金属
        "au", "ag",
        # 能化
        "sc", "fu", "bu", "ru", "sp", "eb", "pg",
        # 农产品
        "p", "y", "m", "a", "c", "cs", "l", "v", "pp",
        "ma", "ta", "eg",
    }

    def __init__(
        self,
        backtest_url: str = "http://192.168.31.142:8103",
        timeout: float = 600.0,
        data_url: str = "http://192.168.31.74:8105",
    ):
        """初始化 TqSdk 回测客户端

        Args:
            backtest_url: 保留兼容的旧参数，内部执行路径不再使用
            timeout: 回测超时时间（秒）
            data_url: Mini data API 地址（用于合约解析）
        """
        self.backtest_url = backtest_url.rstrip("/")
        self.timeout = timeout
        self._settings = get_settings()
        self._strategy_root = self._settings.tqsdk_strategy_yaml_dir.expanduser().resolve()
        self._strategy_root.mkdir(parents=True, exist_ok=True)
        self._runner = OnlineBacktestRunner(settings=self._settings)
        # 与 air backtest 服务 _run_backtest_background 对齐：
        # 不走 OnlineBacktestRunner.submit/_execute/wait_for_job 这条 asyncio 调度路径，
        # submit_backtest 只准备 job_input，poll_result 才在 to_thread 里同步直跑 run_job_sync。
        self._pending_jobs: dict[str, BacktestJobInput] = {}

        # 导入合约解析器
        from .contract_resolver import ContractResolver
        self._contract_resolver = ContractResolver(data_url)

    async def submit_backtest(
        self,
        yaml_path: str | Path,
        start_date: str,
        end_date: str,
        initial_capital: float = 500000.0,
    ) -> str:
        """提交回测任务

        Args:
            yaml_path: 策略 YAML 文件路径
            start_date: 回测开始日期 (YYYY-MM-DD)
            end_date: 回测结束日期 (YYYY-MM-DD)
            initial_capital: 初始资金

        Returns:
            task_id: 回测任务 ID

        Raises:
            TqSdkBacktestError: 提交失败
        """
        yaml_path = Path(yaml_path)
        if not yaml_path.exists():
            raise TqSdkBacktestError(f"YAML 文件不存在: {yaml_path}")

        # 1. 读取并验证 YAML
        with open(yaml_path, "r", encoding="utf-8") as f:
            strategy = yaml.safe_load(f)

        is_valid, errors = self.validate_yaml(strategy)
        if not is_valid:
            raise TqSdkBacktestError(f"YAML 验证失败: {', '.join(errors)}")

        # 2. 预处理 YAML（主力合约转换）
        strategy = await self._preprocess_yaml(strategy)

        # 3. 预处理后的 YAML 写入 formal runner 运行目录
        strategy_name = strategy.get("name", yaml_path.stem)
        symbols = strategy.get("symbols", [])
        if not symbols:
            raise TqSdkBacktestError("YAML 缺少 symbols 字段")
        if len(symbols) > 1:
            logger.warning("TqSdk formal runner 当前只使用首个 symbol: %s", symbols)

        runtime_yaml_path, strategy_yaml_filename = self._persist_runtime_yaml(yaml_path, strategy)
        task_id = f"tqsdk-{runtime_yaml_path.stem}-{id(self):x}-{len(symbols)}"

        payload = {
            "job_id": task_id,
            "strategy_template_id": str(strategy.get("template_id") or "generic"),
            "strategy_yaml_filename": strategy_yaml_filename,
            "symbol": str(symbols[0]),
            "start_date": start_date,
            "end_date": end_date,
            "initial_capital": initial_capital,
        }

        try:
            logger.info("准备内部 TqSdk 回测任务: %s (%s ~ %s)", strategy_name, start_date, end_date)
            # 只做规范化与登记，不进 asyncio 调度链路；真正执行放到 poll_result 内 to_thread 同步直跑
            job_input = BacktestJobInput.from_mapping(payload)
            self._pending_jobs[task_id] = job_input
            logger.info(f"✅ TqSdk 回测任务已登记: task_id={task_id}")
            return task_id
        except (BacktestExecutionError, ValueError) as exc:
            raise TqSdkBacktestError(f"提交回测失败: {exc}") from exc
        except Exception as e:
            raise TqSdkBacktestError(f"提交回测异常: {e}") from e

    async def poll_result(
        self,
        task_id: str,
        poll_interval: float = 10.0,
        max_wait: Optional[float] = None,
    ) -> dict[str, Any]:
        """轮询获取回测结果

        Args:
            task_id: 回测任务 ID
            poll_interval: 轮询间隔（秒）
            max_wait: 最大等待时间（秒），None 表示使用 self.timeout

        Returns:
            回测结果字典

        Raises:
            TqSdkBacktestError: 回测失败或超时
        """
        _ = poll_interval
        max_wait = max_wait or self.timeout

        job_input = self._pending_jobs.pop(task_id, None)
        if job_input is None:
            raise TqSdkBacktestError(f"回测任务不存在: task_id={task_id}")

        logger.info("运行内部 TqSdk 回测: task_id=%s (最大等待 %ss)", task_id, max_wait)

        # 与 air backtest 服务 _run_backtest_background 对齐：
        # 单次 to_thread 同步直跑 run_job_sync，不进 asyncio.create_task / Semaphore / wait_for_job 链路。
        try:
            report = await asyncio.wait_for(
                asyncio.to_thread(self._runner.run_job_sync, job_input),
                timeout=max_wait,
            )
        except asyncio.TimeoutError as exc:
            raise TqSdkBacktestError(f"回测超时 ({max_wait}s): task_id={task_id}") from exc
        except BacktestExecutionError as exc:
            raise TqSdkBacktestError(f"回测执行失败: {exc}") from exc
        except Exception as exc:  # noqa: BLE001
            raise TqSdkBacktestError(f"回测执行异常: {exc}") from exc

        if report is None:
            raise TqSdkBacktestError(f"回测未返回报告: task_id={task_id}")

        if report.status == "failed":
            raise TqSdkBacktestError(report.failure_reason or f"回测失败: {task_id}")

        result = report.to_formal_report_v1()
        result["status"] = report.status
        result["task_id"] = task_id
        logger.info("✅ TqSdk 回测完成: task_id=%s", task_id)
        return result

    def validate_yaml(self, strategy: dict) -> tuple[bool, list[str]]:
        """验证 YAML 是否符合 TqSdk 标准

        Args:
            strategy: 策略配置字典

        Returns:
            (是否通过, 错误列表)
        """
        errors = []

        # 必填字段检查
        required_fields = [
            ("symbols", "交易品种"),
            ("timeframe_minutes", "K线周期"),
            ("factors", "因子列表"),
            ("signal", "信号规则"),
            ("transaction_costs", "交易成本"),
        ]

        for field, desc in required_fields:
            if field not in strategy or not strategy[field]:
                errors.append(f"缺少必填字段: {field} ({desc})")

        # transaction_costs 子字段检查
        if "transaction_costs" in strategy:
            tc = strategy["transaction_costs"]
            if "slippage_per_unit" not in tc:
                errors.append("transaction_costs 缺少 slippage_per_unit")
            if "commission_per_lot_round_turn" not in tc:
                errors.append("transaction_costs 缺少 commission_per_lot_round_turn")

        # risk 字段检查
        risk = strategy.get("risk", {})
        if risk.get("force_close_day") != "14:55":
            errors.append("risk.force_close_day 必须为 14:55")
        if not risk.get("no_overnight"):
            errors.append("risk.no_overnight 必须为 true")

        # 夜盘品种检查 force_close_night
        symbols = strategy.get("symbols", [])
        if symbols:
            # 提取品种代码（去除交易所前缀）
            for symbol in symbols:
                commodity = symbol.split(".")[-1] if "." in symbol else symbol
                commodity = str(commodity).lower()
                if commodity.endswith("_main"):
                    commodity = commodity[:-5]
                else:
                    commodity = re.sub(r"\d+$", "", commodity)

                if commodity in self.NIGHT_TRADING_COMMODITIES:
                    if not risk.get("force_close_night"):
                        errors.append(f"夜盘品种 {commodity} 必须设置 risk.force_close_night")
                    break  # 只要有一个夜盘品种就检查

        # 禁止字段检查（TqSdk 不支持）
        forbidden_fields = [
            ("stop_loss_yuan", "固定金额止损"),
            ("take_profit_yuan", "固定金额止盈"),
        ]

        for field, desc in forbidden_fields:
            if field in strategy:
                errors.append(f"禁止使用字段: {field} ({desc})，TqSdk 不支持")
            if field in risk:
                errors.append(f"禁止使用 risk.{field} ({desc})，请改用 risk.stop_loss/risk.take_profit ATR 配置")

        # 止损止盈类型检查：统一从 risk 块读取，与 local engine 保持一致
        if "stop_loss" in strategy:
            errors.append("stop_loss 必须位于 risk 块内部，不能放在根级")
        if "take_profit" in strategy:
            errors.append("take_profit 必须位于 risk 块内部，不能放在根级")

        stop_loss = risk.get("stop_loss", {})
        if not stop_loss:
            errors.append("risk.stop_loss 为必填项")
        elif stop_loss.get("type") not in ("atr", None):
            errors.append(f"risk.stop_loss.type 必须为 'atr'，当前为 '{stop_loss.get('type')}'")

        take_profit = risk.get("take_profit", {})
        if not take_profit:
            errors.append("risk.take_profit 为必填项")
        elif take_profit.get("type") not in ("atr", None):
            errors.append(f"risk.take_profit.type 必须为 'atr'，当前为 '{take_profit.get('type')}'")

        return len(errors) == 0, errors

    async def _preprocess_yaml(self, strategy: dict) -> dict:
        """预处理 YAML（主力合约转换等）

        Args:
            strategy: 原始策略配置

        Returns:
            预处理后的策略配置
        """
        strategy = dict(strategy)  # 复制，避免修改原始数据

        # 主力合约转换（DCE.p0 → DCE.p2505）
        symbols = strategy.get("symbols", [])
        converted_symbols = []

        for symbol in symbols:
            # 支持三种需要解析的格式：
            # 1. _main 通配符（如 SHFE.rb_main、DCE.m_main）→ 当前主力合约
            # 2. 以 0 结尾的指数合约（如 DCE.p0、SHFE.rb0）→ 当前主力合约
            # 3. 无交易所前缀的品种代码（如 rb、m）→ 自动补全交易所并解析
            needs_resolve = (
                "_main" in symbol
                or symbol.endswith(".0")
                or (".".join(symbol.split(".")[1:]) if "." in symbol else symbol).rstrip("0123456789") != (".".join(symbol.split(".")[1:]) if "." in symbol else symbol) and symbol.endswith("0")
            )
            # 简化判断：_main 结尾 或 合约代码末尾是 0（指数合约）
            base = symbol.split(".")[-1] if "." in symbol else symbol
            needs_resolve = "_main" in base or base.endswith("0")

            if needs_resolve:
                # 统一转换为 EXCHANGE.commodity0 格式供 resolver 处理
                if "_main" in symbol:
                    # SHFE.rb_main → SHFE.rb0
                    resolve_symbol = symbol.replace("_main", "0")
                else:
                    resolve_symbol = symbol
                try:
                    main_contract = await self._contract_resolver.get_main_contract(resolve_symbol)
                    logger.info(f"主力合约解析: {symbol} → {main_contract}")
                    converted_symbols.append(main_contract)
                except Exception as e:
                    logger.warning(f"主力合约解析失败 ({symbol}): {e}，保持原值")
                    converted_symbols.append(symbol)
            else:
                converted_symbols.append(symbol)

        strategy["symbols"] = converted_symbols

        return strategy

    async def close(self):
        """关闭客户端"""
        await self._contract_resolver.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    def _persist_runtime_yaml(self, source_path: Path, strategy: dict[str, Any]) -> tuple[Path, str]:
        if self._strategy_root == source_path.parent or self._strategy_root in source_path.parents:
            relative_path = source_path.relative_to(self._strategy_root)
        else:
            relative_path = Path(source_path.name)

        target_path = self._strategy_root / "_tqsdk_runtime" / relative_path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        with target_path.open("w", encoding="utf-8") as handle:
            yaml.safe_dump(
                strategy,
                handle,
                allow_unicode=True,
                sort_keys=False,
                default_flow_style=False,
            )
        return target_path, target_path.relative_to(self._strategy_root).as_posix()
