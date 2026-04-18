"""TqSdk 回测客户端 — TASK-0127

通过 HTTP API 调用 Studio backtest 服务进行 TqSdk 在线回测。

功能：
1. 提交回测任务到 Studio backtest (http://192.168.31.142:8103)
2. 轮询获取回测结果
3. YAML 预处理与验证（TqSdk 兼容性检查）
4. 主力合约代码转换
"""
from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import httpx
import yaml

logger = logging.getLogger(__name__)


class TqSdkBacktestError(Exception):
    """TqSdk 回测异常"""
    pass


class TqSdkBacktestClient:
    """TqSdk 回测客户端（通过 Studio backtest API）"""

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
        data_url: str = "http://192.168.31.76:8105",
    ):
        """初始化 TqSdk 回测客户端

        Args:
            backtest_url: Studio backtest 服务地址
            timeout: 回测超时时间（秒）
            data_url: Mini data API 地址（用于合约解析）
        """
        self.backtest_url = backtest_url.rstrip("/")
        self.timeout = timeout
        self._client = httpx.AsyncClient(timeout=30.0)

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

        # 3. 构建请求参数
        strategy_name = strategy.get("name", yaml_path.stem)
        symbols = strategy.get("symbols", [])
        if not symbols:
            raise TqSdkBacktestError("YAML 缺少 symbols 字段")

        payload = {
            "strategy_id": "generic",  # 映射到 generic_formal_strategy_v1
            "strategy_name": strategy_name,
            "engine_type": "tqsdk",
            "start": start_date,
            "end": end_date,
            "symbols": symbols,
            "initial_capital": initial_capital,
            "params": strategy,
        }

        # 4. 提交回测任务
        try:
            url = f"{self.backtest_url}/api/backtest/run"
            logger.info(f"提交 TqSdk 回测任务: {strategy_name} ({start_date} ~ {end_date})")

            response = await self._client.post(url, json=payload)
            response.raise_for_status()

            result = response.json()
            task_id = result.get("task_id")

            if not task_id:
                raise TqSdkBacktestError(f"未返回 task_id: {result}")

            logger.info(f"✅ TqSdk 回测任务已提交: task_id={task_id}")
            return task_id

        except httpx.HTTPStatusError as e:
            error_detail = e.response.text[:200] if e.response else str(e)
            raise TqSdkBacktestError(f"提交回测失败 ({e.response.status_code}): {error_detail}") from e
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
        max_wait = max_wait or self.timeout
        start_time = asyncio.get_event_loop().time()
        url = f"{self.backtest_url}/api/backtest/results/{task_id}"

        logger.info(f"开始轮询 TqSdk 回测结果: task_id={task_id} (最大等待 {max_wait}s)")

        while True:
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed > max_wait:
                raise TqSdkBacktestError(f"回测超时 ({max_wait}s): task_id={task_id}")

            try:
                response = await self._client.get(url)
                response.raise_for_status()
                result = response.json()

                status = result.get("status", "unknown")

                if status == "completed":
                    logger.info(f"✅ TqSdk 回测完成: task_id={task_id}")
                    return result

                elif status == "failed":
                    error = result.get("error", "未知错误")
                    raise TqSdkBacktestError(f"回测失败: {error}")

                elif status in ("pending", "running"):
                    logger.debug(f"回测进行中 ({status}): {elapsed:.1f}s / {max_wait}s")
                    await asyncio.sleep(poll_interval)

                else:
                    logger.warning(f"未知回测状态: {status}")
                    await asyncio.sleep(poll_interval)

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    raise TqSdkBacktestError(f"回测任务不存在: task_id={task_id}") from e
                raise TqSdkBacktestError(f"查询回测结果失败: {e}") from e
            except TqSdkBacktestError:
                raise
            except Exception as e:
                logger.warning(f"轮询异常，继续重试: {e}")
                await asyncio.sleep(poll_interval)

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
                # 去除合约月份，只保留品种代码
                commodity = "".join([c for c in commodity if c.isalpha()]).lower()

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

        # 止损止盈类型检查
        stop_loss = strategy.get("stop_loss", {})
        if stop_loss and stop_loss.get("type") not in ("atr", None):
            errors.append(f"stop_loss.type 必须为 'atr'，当前为 '{stop_loss.get('type')}'")

        take_profit = strategy.get("take_profit", {})
        if take_profit and take_profit.get("type") not in ("atr", None):
            errors.append(f"take_profit.type 必须为 'atr'，当前为 '{take_profit.get('type')}'")

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
            # 如果是主力合约代码（以 0 结尾），需要转换
            if symbol.endswith(".0") or symbol.endswith("0"):
                try:
                    # 调用合约解析器进行转换
                    main_contract = await self._contract_resolver.get_main_contract(symbol)
                    logger.info(f"主力合约转换: {symbol} → {main_contract}")
                    converted_symbols.append(main_contract)
                except Exception as e:
                    logger.warning(f"主力合约转换失败 ({symbol}): {e}，保持原值")
                    converted_symbols.append(symbol)
            else:
                converted_symbols.append(symbol)

        strategy["symbols"] = converted_symbols

        return strategy

    async def close(self):
        """关闭客户端"""
        await self._client.aclose()
        await self._contract_resolver.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
