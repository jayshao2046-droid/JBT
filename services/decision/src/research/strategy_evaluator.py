"""策略完整评估流水线 — TASK-0121-A

实现五阶段策略评估流程：
1. 基础合规性检查（30 分）
2. 回测评估（30 分）
3. PBO 过拟合检测（10 分）
4. 因子有效性验证（10 分）
5. 风控严格度评估（20 分）

评分标准：
- S 级（90-100）：可直接上线
- A 级（80-89）：小幅调整后上线
- B 级（70-79）：优化后上线
- C 级（60-69）：大幅优化
- D 级（< 60）：禁止上线
"""
from __future__ import annotations

import math
import yaml
from pathlib import Path
from datetime import datetime
from typing import Any, Optional

from .sandbox_engine import SandboxEngine
from .pbo_validator import PBOValidator
from .factor_validator import FactorValidator
from .yaml_signal_executor import YAMLSignalExecutor


class StrategyEvaluator:
    """策略完整评估流水线 — TASK-0122-B 修正版"""

    def __init__(
        self,
        data_service_url: str = "http://192.168.31.74:8105",
        ollama_url: str = "http://192.168.31.142:11434",
    ):
        self.sandbox = SandboxEngine(data_service_url)
        self.pbo_validator = PBOValidator()
        self.factor_validator = FactorValidator()
        self.yaml_executor = YAMLSignalExecutor(
            data_service_url=data_service_url,
            ollama_url=ollama_url,
        )

    async def evaluate_strategy(
        self,
        strategy_path: str,
        start_date: str,
        end_date: str,
    ) -> dict[str, Any]:
        """完整评估单个策略。

        Args:
            strategy_path: 策略 YAML 文件路径
            start_date: 回测开始日期（YYYY-MM-DD）
            end_date: 回测结束日期（YYYY-MM-DD）

        Returns:
            评估报告（JSON 格式）
        """
        # 1. 读取策略配置
        with open(strategy_path, 'r', encoding='utf-8') as f:
            strategy = yaml.safe_load(f)

        strategy_id = Path(strategy_path).stem

        # 2. 基础合规性检查（30 分）
        basic_score, basic_report = self._check_basic_compliance(strategy)

        # 3. 回测评估（30 分）— 调用 YAMLSignalExecutor，预生成代码供后续复用
        backtest_result = await self.yaml_executor.execute(strategy, start_date, end_date)
        backtest_score, backtest_report = self._score_backtest_result(backtest_result)
        # 缓存 bars + code 供后续阶段复用
        _bars = backtest_result.equity_curve  # equity curve 用于 PBO
        _code = backtest_result.generated_code

        # 4. PBO 过拟合检测（10 分）
        pbo_score, pbo_report = await self._run_pbo_validation(
            strategy, start_date, end_date, backtest_result
        )

        # 5. 因子有效性验证（10 分）
        factor_score, factor_report = await self._run_factor_validation(
            strategy, start_date, end_date
        )

        # 6. 风控严格度评估（20 分）
        risk_score, risk_report = self._evaluate_risk_strictness(strategy)

        # 7. 计算总分
        total_score = (
            basic_score + backtest_score + pbo_score +
            factor_score + risk_score
        )

        # 8. 风控加分/扣分
        bonus, penalty = self._calculate_risk_bonus_penalty(strategy)
        final_score = max(0, min(100, total_score + bonus - penalty))

        # 9. 确定等级
        grade = self._determine_grade(final_score)

        # 10. 生成报告
        report = {
            'strategy_id': strategy_id,
            'evaluation_time': datetime.now().isoformat(),
            'final_score': final_score,
            'grade': grade,
            'breakdown': {
                'basic': {'score': basic_score, 'max': 30, 'report': basic_report},
                'backtest': {'score': backtest_score, 'max': 30, 'report': backtest_report},
                'pbo': {'score': pbo_score, 'max': 10, 'report': pbo_report},
                'factor': {'score': factor_score, 'max': 10, 'report': factor_report},
                'risk': {'score': risk_score, 'max': 20, 'report': risk_report},
            },
            'risk_adjustment': {
                'bonus': bonus,
                'penalty': penalty,
            },
            'conclusion': self._generate_conclusion(final_score, grade, backtest_report, risk_report),
        }

        return report

    def _check_basic_compliance(self, strategy: dict) -> tuple[int, dict]:
        """基础合规性检查：30 分。

        检查项：
        - 因子权重和 ≈ 1.0（10 分）
        - 信号阈值合理性（10 分）
        - 风控参数完整性（10 分）
        """
        score = 0
        report = {}

        # 因子权重和（factors 是 list，非 dict）
        factors = strategy.get('factors', [])
        if factors:
            weight_sum = sum(f.get('weight', 0) for f in factors)
            if abs(weight_sum - 1.0) < 0.05:
                score += 10
                report['weight_sum'] = {'status': 'pass', 'value': round(weight_sum, 4)}
            else:
                report['weight_sum'] = {'status': 'fail', 'value': round(weight_sum, 4), 'expected': 1.0}
        else:
            report['weight_sum'] = {'status': 'fail', 'value': 0.0, 'reason': 'no factors defined'}

        # 信号阈值（来自 signal 块）
        signal = strategy.get('signal', {})
        long_th = float(signal.get('long_threshold', 0))
        short_th = float(signal.get('short_threshold', 0))
        if 0.3 <= long_th <= 0.9 and -0.9 <= short_th <= -0.3:
            score += 10
            report['thresholds'] = {'status': 'pass', 'long': long_th, 'short': short_th}
        else:
            report['thresholds'] = {
                'status': 'warn',
                'long': long_th,
                'short': short_th,
                'note': 'threshold range 0.3-0.9 / -0.9 to -0.3 recommended',
            }
            score += 5  # 阈值不是硬性要求，给部分分

        # 风控参数完整性（匹配真实 YAML risk 字段）
        risk = strategy.get('risk', {})
        required_params = [
            'daily_loss_limit_yuan',
            'max_drawdown_pct',
        ]
        present = [p for p in required_params if p in risk]
        if len(present) == len(required_params):
            score += 10
            report['risk_params'] = {'status': 'pass', 'params': list(risk.keys())}
        elif present:
            score += 5
            missing = [p for p in required_params if p not in risk]
            report['risk_params'] = {'status': 'warn', 'present': present, 'missing': missing}
        else:
            missing = required_params
            report['risk_params'] = {'status': 'fail', 'missing': missing}

        # ── 硬性约束 1：禁止隔夜（no_overnight: true）──
        no_overnight = bool(risk.get('no_overnight', False))
        if no_overnight:
            report['no_overnight'] = {'status': 'pass'}
        else:
            report['no_overnight'] = {'status': 'fail', 'reason': 'no_overnight 必须为 true，禁止隔夜'}

        # ── 硬性约束 2：夜盘可做（force_close_night 必须有值）──
        force_close_night = risk.get('force_close_night', '')
        if force_close_night:
            report['night_session'] = {'status': 'pass', 'close_at': force_close_night}
        else:
            report['night_session'] = {'status': 'warn', 'reason': 'force_close_night 未设置，夜盘无强平保障'}

        # ── 硬性约束 3：日盘 14:55 必须强平──
        force_close_day = risk.get('force_close_day', '')
        if force_close_day == '14:55':
            report['force_close_day'] = {'status': 'pass', 'close_at': force_close_day}
        elif force_close_day:
            report['force_close_day'] = {
                'status': 'fail',
                'close_at': force_close_day,
                'reason': f'force_close_day 为 {force_close_day}，必须设为 14:55',
            }
        else:
            report['force_close_day'] = {'status': 'fail', 'reason': 'force_close_day 未设置，日盘无 14:55 强平保障'}

        return score, report

    def _score_backtest_result(self, result: Any) -> tuple[int, dict]:
        """将 SignalBacktestResult 转换为评分和报告（供 evaluate_strategy 使用）。"""
        from .yaml_signal_executor import SignalBacktestResult
        if isinstance(result, SignalBacktestResult) and result.status == "failed":
            return 0, {
                'status': 'failed',
                'error': result.error,
                'sharpe_ratio': 0.0,
                'max_drawdown': 1.0,
                'win_rate': 0.0,
            }
        sharpe = getattr(result, 'sharpe_ratio', 0.0)
        max_dd = getattr(result, 'max_drawdown', 1.0)
        win_rate = getattr(result, 'win_rate', 0.0)

        score = 0
        if sharpe >= 3.0:   score += 10
        elif sharpe >= 2.5: score += 8
        elif sharpe >= 2.0: score += 6
        elif sharpe >= 1.5: score += 4
        elif sharpe >= 1.0: score += 2

        if max_dd <= 0.01:   score += 10
        elif max_dd <= 0.015: score += 8
        elif max_dd <= 0.02:  score += 6
        elif max_dd <= 0.03:  score += 3

        if win_rate >= 0.60:   score += 10
        elif win_rate >= 0.55: score += 8
        elif win_rate >= 0.50: score += 6
        elif win_rate >= 0.45: score += 3

        report = {
            'sharpe_ratio': sharpe,
            'max_drawdown': max_dd,
            'win_rate': win_rate,
            'total_return': getattr(result, 'total_return', 0.0),
            'annualized_return': getattr(result, 'annualized_return', 0.0),
            'trades_count': getattr(result, 'trades_count', 0),
            'final_capital': getattr(result, 'final_capital', 0.0),
            'status': 'success',
        }
        return score, report

    async def _run_backtest_evaluation(
        self, strategy: dict, start_date: str, end_date: str
    ) -> tuple[int, dict]:
        """回测评估（兼容旧调用路径，内部调用 yaml_executor）。"""
        try:
            result = await self.yaml_executor.execute(strategy, start_date, end_date)

            return self._score_backtest_result(result)

        except Exception as e:
            return 0, {
                'status': 'failed',
                'error': str(e),
                'sharpe_ratio': 0.0,
                'max_drawdown': 1.0,
                'win_rate': 0.0,
            }

    async def _run_pbo_validation(
        self,
        strategy: dict,
        start_date: str,
        end_date: str,
        backtest_result: Any = None,
    ) -> tuple[int, dict]:
        """PBO 时序稳定性检验：10 分。

        用已有 equity_curve 切分 4 个季度，统计各季度 Sharpe 正比例。
        比例 >= 0.75 → 10 分；>= 0.5 → 6 分；>= 0.25 → 3 分。
        """
        try:
            from .yaml_signal_executor import SignalBacktestResult
            if (
                backtest_result is None
                or not isinstance(backtest_result, SignalBacktestResult)
                or backtest_result.status == 'failed'
                or len(backtest_result.equity_curve) < 40
            ):
                return 3, {'status': 'skipped', 'reason': '回测失败或数据不足，无法做时序稳定性检验'}

            curve = backtest_result.equity_curve
            n = len(curve)
            q = n // 4
            positive_quarters = 0
            quarterly_sharpes = []

            for i in range(4):
                seg = curve[i * q: (i + 1) * q + 1]
                if len(seg) < 5:
                    continue
                returns = [
                    (seg[j] - seg[j - 1]) / seg[j - 1]
                    for j in range(1, len(seg))
                    if seg[j - 1] > 0
                ]
                if not returns:
                    quarterly_sharpes.append(0.0)
                    continue
                mean_r = sum(returns) / len(returns)
                var_r = sum((r - mean_r) ** 2 for r in returns) / len(returns)
                std_r = var_r ** 0.5
                seg_sharpe = (mean_r / std_r * (len(returns) ** 0.5)) if std_r > 1e-10 else 0.0
                quarterly_sharpes.append(round(seg_sharpe, 4))
                if seg_sharpe > 0:
                    positive_quarters += 1

            ratio = positive_quarters / 4
            if ratio >= 0.75:
                score = 10
            elif ratio >= 0.50:
                score = 6
            elif ratio >= 0.25:
                score = 3
            else:
                score = 0

            report = {
                'status': 'completed',
                'method': 'temporal_stability_4q',
                'positive_quarters': positive_quarters,
                'total_quarters': 4,
                'stability_ratio': round(ratio, 3),
                'quarterly_sharpes': quarterly_sharpes,
            }

        except Exception as e:
            score = 0
            report = {'status': 'failed', 'error': str(e)}

        return score, report

    async def _run_factor_validation(
        self, strategy: dict, start_date: str, end_date: str
    ) -> tuple[int, dict]:
        """因子有效性验证：10 分。

        从真实 K 线数据计算主因子的动量 IC（因子值与前向 1 根 bar 收益的 Pearson 相关），
        并调用 FactorValidator 做统计显著性检验。
        """
        try:
            symbol = self.yaml_executor._extract_symbol(strategy)
            tf = int(strategy.get('timeframe_minutes', 60))
            bars = await self.yaml_executor._fetch_bars(symbol, start_date, end_date, tf)

            if len(bars) < 50:
                return 3, {'status': 'skipped', 'reason': f'数据不足 {len(bars)} 根'}

            closes = [float(b.get('close', 0) or 0) for b in bars]

            # 取主因子的 period 参数（优先 fast_period 或 period）
            factors = strategy.get('factors', [])
            primary_period = 10
            for f in factors:
                p = f.get('params', {})
                primary_period = int(p.get('fast_period', p.get('period', primary_period)))
                break
            period = max(2, min(primary_period, len(closes) // 5))

            # 动量因子：close[i] / close[i-period] - 1
            factor_series = []
            return_series = []
            for i in range(period, len(closes) - 1):
                if closes[i - period] > 0 and closes[i] > 0:
                    momentum = closes[i] / closes[i - period] - 1
                    fwd_ret = (closes[i + 1] - closes[i]) / closes[i]
                    factor_series.append(momentum)
                    return_series.append(fwd_ret)

            if len(factor_series) < 20:
                return 3, {'status': 'skipped', 'reason': '因子样本数不足 20'}

            # 调用 FactorValidator 做统计检验
            factor_name = factors[0].get('factor_name', 'momentum') if factors else 'momentum'
            val_result = self.factor_validator.validate(
                factor_name=factor_name,
                symbol=symbol,
                factor_series=factor_series,
                return_series=return_series,
            )

            ic_ir = val_result.ic_ir
            if ic_ir >= 0.3:
                score = 10
            elif ic_ir >= 0.2:
                score = 6
            elif ic_ir >= 0.1:
                score = 3
            else:
                score = 0

            report = {
                'status': 'completed',
                'factor_name': factor_name,
                'ic_mean': round(val_result.ic_mean, 6),
                'ic_std': round(val_result.ic_std, 6),
                'ic_ir': round(ic_ir, 4),
                't_stat': round(val_result.t_stat, 4),
                'p_value': round(val_result.p_value, 4),
                'ls_return': round(val_result.ls_return, 6),
                'passed': val_result.passed,
                'samples': len(factor_series),
            }

        except Exception as e:
            score = 0
            report = {'status': 'failed', 'error': str(e), 'ic_ir': 0.0}

        return score, report

    # ATR 倍数合理范围（按品种波动性分级，总金额 50 万）
    _ATR_MULTIPLIER_RANGE: dict[str, tuple[float, float]] = {
        # 高波动（黑色/有色/贵金属）
        'rb': (1.5, 3.5), 'hc': (1.5, 3.5), 'i': (1.5, 3.5), 'j': (1.5, 3.5), 'jm': (1.5, 3.5),
        'cu': (1.5, 3.5), 'al': (1.5, 3.0), 'zn': (1.5, 3.0), 'ni': (1.5, 3.5), 'ss': (1.5, 3.0),
        'au': (1.2, 3.0), 'ag': (1.5, 3.5),
        # 中波动（能化/油脂/农产品）
        'p': (1.2, 2.8), 'y': (1.2, 2.8), 'm': (1.2, 2.8), 'oi': (1.2, 2.8),
        'v': (1.2, 2.5), 'l': (1.2, 2.5), 'pp': (1.2, 2.5), 'eb': (1.2, 2.5),
        'ru': (1.5, 3.0), 'sp': (1.5, 3.0), 'bu': (1.2, 2.8), 'fu': (1.2, 2.8),
        'pg': (1.2, 2.8), 'eg': (1.2, 2.8),
        # 低波动（农产品/CZCE）
        'ma': (1.0, 2.5), 'ta': (1.0, 2.5), 'cf': (1.0, 2.5), 'sr': (1.0, 2.5),
        'fg': (1.0, 2.5), 'sa': (1.0, 2.5), 'rm': (1.0, 2.5), 'pf': (1.0, 2.5), 'ur': (1.0, 2.5),
        'a': (1.2, 2.8), 'c': (1.2, 2.5), 'cs': (1.2, 2.5), 'jd': (1.0, 2.5),
        'lh': (1.5, 3.5), 'rr': (1.0, 2.5),
    }

    def _evaluate_risk_strictness(self, strategy: dict) -> tuple[int, dict]:
        """风控严格度评估：20 分。

        评分维度：
        - 回撤阈值（5 分）
        - 日亏损限制 ≤ 2000 元（5 分）
        - 单笔止损 ≤ 1000 元（4 分）
        - ATR 过滤倍数合理性（3 分）
        - 盈亏比 ≥ 2:1（3 分）
        """
        risk = strategy.get('risk', {})
        score = 0
        report: dict = {}

        # ── 回撤阈值（5 分）──
        max_dd_pct = risk.get('max_drawdown_pct', 0.1)
        if max_dd_pct <= 0.008:
            score += 5
        elif max_dd_pct <= 0.01:
            score += 4
        elif max_dd_pct <= 0.015:
            score += 2
        elif max_dd_pct <= 0.02:
            score += 1
        report['max_drawdown_pct'] = {'value': max_dd_pct, 'pass': max_dd_pct <= 0.02}

        # ── 硬性约束 3：单品种每日熔断 ≤ 2000 元（5 分）──
        # 总金额 50 万，每日熔断上限 2000 = 0.4%
        daily_loss = risk.get('daily_loss_limit_yuan', 10000)
        daily_loss_pass = daily_loss <= 2000
        if daily_loss_pass:
            if daily_loss <= 1000:
                score += 5
            elif daily_loss <= 1500:
                score += 4
            else:  # <= 2000
                score += 3
        report['daily_loss_limit_yuan'] = {
            'value': daily_loss,
            'hard_cap': 2000,
            'pass': daily_loss_pass,
            'status': 'pass' if daily_loss_pass else 'FAIL — 超出 2000 元上限',
        }

        # ── 硬性约束 4：单笔止损 ≤ 1000 元（4 分）──
        # 用 per_symbol_fuse_yuan 作为单笔止损代理
        per_trade_stop = risk.get('per_symbol_fuse_yuan', risk.get('per_trade_stop_yuan', 10000))
        trade_stop_pass = per_trade_stop <= 1000
        if trade_stop_pass:
            if per_trade_stop <= 500:
                score += 4
            elif per_trade_stop <= 800:
                score += 3
            else:  # <= 1000
                score += 2
        report['per_trade_stop_yuan'] = {
            'value': per_trade_stop,
            'hard_cap': 1000,
            'pass': trade_stop_pass,
            'status': 'pass' if trade_stop_pass else 'FAIL — 单笔止损超出 1000 元上限',
        }

        # ── 硬性约束 5：ATR 过滤倍数合理性（3 分）──
        pos_adj = strategy.get('position_adjustment', {})
        atr_mul = float(pos_adj.get('atr_multiplier', 0))
        symbol_raw = ''
        syms = strategy.get('symbols', [])
        if syms:
            raw = str(syms[0])
            import re as _re
            m = _re.search(r'\.([A-Za-z]+)', raw)
            symbol_raw = m.group(1).lower() if m else ''
        lo, hi = self._ATR_MULTIPLIER_RANGE.get(symbol_raw, (1.0, 3.5))
        atr_ok = (atr_mul == 0) or (lo <= atr_mul <= hi)
        if atr_mul > 0:
            score += 3 if atr_ok else 0
        else:
            score += 1  # 未设置 ATR 过滤，给少量分但不满分
        report['atr_multiplier'] = {
            'value': atr_mul,
            'symbol': symbol_raw,
            'recommended_range': [lo, hi],
            'pass': atr_ok,
            'status': 'pass' if atr_ok else f'WARN — 建议 ATR 倍数 {lo}~{hi}',
        }

        # ── 硬性约束 6：盈亏比 ≥ 2:1（3 分）──
        # 通过 risk_reward_ratio 字段，或从 daily_loss / per_trade_stop 估算
        rr_ratio = float(risk.get('risk_reward_ratio', 0))
        if rr_ratio == 0 and per_trade_stop > 0:
            # 用仓位 * 收益估算：position_fraction * close_est / per_trade_stop
            # 简化：用 daily_loss_limit / per_trade_stop 作为粗略盈亏比
            rr_ratio = round(daily_loss / per_trade_stop, 2) if per_trade_stop > 0 else 0
        rr_pass = rr_ratio >= 2.0
        if rr_ratio >= 3.0:
            score += 3
        elif rr_ratio >= 2.0:
            score += 2
        elif rr_ratio >= 1.5:
            score += 1
        report['risk_reward_ratio'] = {
            'value': rr_ratio,
            'minimum': 2.0,
            'pass': rr_pass,
            'status': 'pass' if rr_pass else f'WARN — 盈亏比 {rr_ratio:.1f}:1，建议 ≥ 2:1',
        }

        return score, report

    def _calculate_risk_bonus_penalty(self, strategy: dict) -> tuple[int, int]:
        """计算风控加分/扣分。

        加分项（最多 +10 分）：仓位≤5%、日亏损≤0.3%、熔断≤0.5%、回撤≤1.5%
        扣分项（最多 -20 分）：仓位>15%、日亏损>1.0%、熔断>1.5%、回撤>3.0%
        """
        risk = strategy.get('risk', {})
        bonus = 0
        penalty = 0

        # 加分项（position_fraction 在顶层）
        position = float(strategy.get('position_fraction', risk.get('max_position_per_symbol', 0.1)))
        if position <= 0.05:
            bonus += 3

        daily_loss_pct = risk.get('daily_loss_limit_yuan', 10000) / 500000
        if daily_loss_pct <= 0.003:
            bonus += 3

        fuse_pct = risk.get('per_symbol_fuse_yuan', 10000) / 500000
        if fuse_pct <= 0.005:
            bonus += 2

        max_dd_pct = risk.get('max_drawdown_pct', 0.1)
        if max_dd_pct <= 0.015:
            bonus += 2

        # 扣分项
        if position > 0.15:
            penalty += 10

        if daily_loss_pct > 0.01:
            penalty += 5

        if fuse_pct > 0.015:
            penalty += 3

        if max_dd_pct > 0.03:
            penalty += 2

        # ── 硬性约束违规重罚 ──
        # 每日熔断超 2000 元 → -10 分
        daily_loss_abs = risk.get('daily_loss_limit_yuan', 10000)
        if daily_loss_abs > 2000:
            penalty += 10

        # 单笔止损超 1000 元 → -8 分
        per_trade_stop = risk.get('per_symbol_fuse_yuan', risk.get('per_trade_stop_yuan', 10000))
        if per_trade_stop > 1000:
            penalty += 8

        # 未设置禁止隔夜 → -5 分
        if not bool(risk.get('no_overnight', False)):
            penalty += 5

        # force_close_day 不等于 14:55 → -8 分
        if risk.get('force_close_day', '') != '14:55':
            penalty += 8

        return bonus, penalty

    def _determine_grade(self, score: int) -> str:
        """确定等级。

        Args:
            score: 最终得分

        Returns:
            等级（S/A/B/C/D）
        """
        if score >= 90:
            return 'S'
        elif score >= 80:
            return 'A'
        elif score >= 70:
            return 'B'
        elif score >= 60:
            return 'C'
        else:
            return 'D'

    def _generate_conclusion(
        self, score: int, grade: str, backtest: dict, risk: dict
    ) -> dict:
        """生成结论和建议。

        Args:
            score: 最终得分
            grade: 等级
            backtest: 回测报告
            risk: 风控报告

        Returns:
            结论字典
        """
        conclusion = {
            'can_deploy': grade in ['S', 'A'],
            'priority': 'high' if grade == 'S' else 'medium' if grade == 'A' else 'low',
            'suggestions': [],
            'warnings': [],
        }

        # 根据回测结果给建议
        if backtest.get('max_drawdown', 0) > 0.015:
            conclusion['suggestions'].append('降低仓位或收紧止损，控制回撤')

        if backtest.get('sharpe_ratio', 0) < 2.5:
            conclusion['suggestions'].append('优化入场时机，提高 Sharpe Ratio')

        if backtest.get('win_rate', 0) < 0.55:
            conclusion['suggestions'].append('提高入场阈值，提升胜率')

        # 根据风控参数给建议
        # risk_report 中字段可能是 {'value': x, 'pass': bool} 或直接是数值
        daily_loss_raw = risk.get('daily_loss_pct', 0)
        daily_loss_val = daily_loss_raw.get('value', 0) if isinstance(daily_loss_raw, dict) else daily_loss_raw
        if daily_loss_val > 0.005:
            conclusion['warnings'].append('日亏损限制过宽松，建议收紧至 0.5%')

        max_dd_raw = risk.get('max_drawdown_pct', 0)
        max_dd_val = max_dd_raw.get('value', 0) if isinstance(max_dd_raw, dict) else max_dd_raw
        if max_dd_val > 0.015:
            conclusion['warnings'].append('回撤阈值过宽松，建议收紧至 1.5%')

        return conclusion

    def generate_markdown_report(self, report: dict) -> str:
        """生成 Markdown 格式报告。

        Args:
            report: 评估报告字典

        Returns:
            Markdown 格式的报告文本
        """
        strategy_id = report['strategy_id']
        score = report['final_score']
        grade = report['grade']
        breakdown = report['breakdown']

        md = f"""# {strategy_id} 策略评估报告

## 综合评分：{score}/100 ({grade} 级)

### 1. 基础合规性（{breakdown['basic']['score']}/30）

{self._format_basic_report(breakdown['basic']['report'])}

### 2. 回测表现（{breakdown['backtest']['score']}/30）

{self._format_backtest_report(breakdown['backtest']['report'])}

### 3. PBO 过拟合检测（{breakdown['pbo']['score']}/10）

{self._format_pbo_report(breakdown['pbo']['report'])}

### 4. 因子有效性（{breakdown['factor']['score']}/10）

{self._format_factor_report(breakdown['factor']['report'])}

### 5. 风控严格度（{breakdown['risk']['score']}/20）

{self._format_risk_report(breakdown['risk']['report'])}

## 风控调整

- 加分：+{report['risk_adjustment']['bonus']}
- 扣分：-{report['risk_adjustment']['penalty']}

## 生产准入建议

{self._format_conclusion(report['conclusion'])}

---
生成时间：{report['evaluation_time']}
"""
        return md

    def _format_basic_report(self, report: dict) -> str:
        """格式化基础合规性报告。"""
        lines = []

        # 权重和
        weight = report.get('weight_sum', {})
        status = '✅' if weight.get('status') == 'pass' else '❌'
        lines.append(f"{status} 因子权重和：{weight.get('value', 0):.3f}")

        # 阈值
        thresh = report.get('thresholds', {})
        status = '✅' if thresh.get('status') == 'pass' else '❌'
        lines.append(f"{status} 阈值合理性：long={thresh.get('long', 0):.2f}, short={thresh.get('short', 0):.2f}")

        # 风控参数
        risk = report.get('risk_params', {})
        status = '✅' if risk.get('status') == 'pass' else '❌'
        if risk.get('status') == 'pass':
            lines.append(f"{status} 风控参数完整")
        else:
            missing = risk.get('missing', [])
            lines.append(f"{status} 风控参数缺失：{', '.join(missing)}")

        return '\n'.join(lines)

    def _format_backtest_report(self, report: dict) -> str:
        """格式化回测报告。"""
        if report.get('status') == 'failed':
            return f"❌ 回测失败：{report.get('error', 'unknown error')}"

        lines = [
            f"- Sharpe Ratio: {report.get('sharpe_ratio', 0):.2f}",
            f"- 最大回撤: {report.get('max_drawdown', 0):.2%}",
            f"- 胜率: {report.get('win_rate', 0):.2%}",
            f"- 总收益: {report.get('total_return', 0):.2%}",
            f"- 交易次数: {report.get('trades_count', 0)}",
        ]
        return '\n'.join(lines)

    def _format_pbo_report(self, report: dict) -> str:
        """格式化 PBO 报告。"""
        if report.get('status') == 'failed':
            return f"❌ PBO 验证失败：{report.get('error', 'unknown error')}"

        pbo = report.get('pbo', 1.0)
        risk_level = report.get('risk_level', 'unknown')

        lines = [
            f"- PBO 值: {pbo:.2%}",
            f"- 风险等级: {risk_level}",
        ]

        if report.get('note'):
            lines.append(f"- 备注: {report['note']}")

        return '\n'.join(lines)

    def _format_factor_report(self, report: dict) -> str:
        """格式化因子报告。"""
        if report.get('status') == 'failed':
            return f"❌ 因子验证失败：{report.get('error', 'unknown error')}"

        lines = [
            f"- IC 均值: {report.get('ic_mean', 0):.3f}",
            f"- IC IR: {report.get('ic_ir', 0):.3f}",
            f"- IC p-value: {report.get('ic_pvalue', 1.0):.3f}",
        ]

        if report.get('note'):
            lines.append(f"- 备注: {report['note']}")

        return '\n'.join(lines)

    def _format_risk_report(self, report: dict) -> str:
        """格式化风控报告。"""
        def _val(v):
            """从 {'value': x, 'pass': bool} 或直接数值中提取值。"""
            return v.get('value', 0) if isinstance(v, dict) else v

        lines = [
            f"- 最大回撤阈值: {_val(report.get('max_drawdown_pct', 0)):.2%}",
            f"- 日亏损限制: {_val(report.get('daily_loss_limit_yuan', 0)):.0f} 元 ({_val(report.get('daily_loss_pct', 0)):.2%})",
            f"- 单品种熔断: {_val(report.get('per_symbol_fuse_yuan', 0)):.0f} 元 ({_val(report.get('fuse_pct', 0)):.2%})",
        ]
        return '\n'.join(lines)

    def _format_conclusion(self, conclusion: dict) -> str:
        """格式化结论。"""
        lines = []

        can_deploy = conclusion.get('can_deploy', False)
        priority = conclusion.get('priority', 'low')

        if can_deploy:
            lines.append(f"✅ **可以上线**（优先级：{priority}）")
        else:
            lines.append(f"❌ **不建议上线**（优先级：{priority}）")

        suggestions = conclusion.get('suggestions', [])
        if suggestions:
            lines.append("\n**优化建议：**")
            for s in suggestions:
                lines.append(f"- {s}")

        warnings = conclusion.get('warnings', [])
        if warnings:
            lines.append("\n**风险警告：**")
            for w in warnings:
                lines.append(f"- {w}")

        return '\n'.join(lines)
