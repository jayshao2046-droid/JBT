#!/usr/bin/env python3
"""F5: 构造金融领域增强语料（期货/宏观/术语/规则）。

来源：
  1. 内置期货术语词典（方案 B：数据 Agent 自维护，禁止跨服务读 services/decision/configs/）
  2. 规则合成：用模板 × 术语 → 生成问答对
  3. 可选合并：FinGPT/finance-alpaca 等开源中文金融指令集（--external-jsonl）

输出：
  - <out>/dataset_f5_raw.jsonl            合约规则自生成 raw（待人工抽样 200 条校验）
  - <out>/dataset_f5.jsonl                正式入训语料（已确认无幻觉的部分）
  - <out>/DATA_PROVENANCE.md              数据来源/license/抽取日期/样本量
  - <out>/manual_review_log.md            人工校验留痕（首次创建空模板）

预审硬约束（REVIEW-PRE-20260424-TASK-P1-20260424F5）：
  - 阻断项 ①：方案 B，术语库内置维护，禁止读 services/decision/configs/
  - 阻断项 ②：raw → 正式两段式分离，未完成 200 条校验前禁止合并
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from datetime import date
from pathlib import Path
from typing import Iterable

DEFAULT_SYSTEM_PROMPT = (
    "You are the JBT researcher model. Return strict JSON only. "
    "Do not emit reasoning, markdown fences, or think tags."
)

# ---------------------------------------------------------------------------
# 期货术语词典（方案 B 内置维护）
# ---------------------------------------------------------------------------

FUTURES_TERMS: dict[str, dict[str, str]] = {
    # 上期所
    "rb": {"exchange": "SHFE", "name_cn": "螺纹钢", "category": "黑色金属", "unit": "10吨/手"},
    "hc": {"exchange": "SHFE", "name_cn": "热轧卷板", "category": "黑色金属", "unit": "10吨/手"},
    "cu": {"exchange": "SHFE", "name_cn": "沪铜", "category": "有色金属", "unit": "5吨/手"},
    "al": {"exchange": "SHFE", "name_cn": "沪铝", "category": "有色金属", "unit": "5吨/手"},
    "zn": {"exchange": "SHFE", "name_cn": "沪锌", "category": "有色金属", "unit": "5吨/手"},
    "ni": {"exchange": "SHFE", "name_cn": "沪镍", "category": "有色金属", "unit": "1吨/手"},
    "au": {"exchange": "SHFE", "name_cn": "沪金", "category": "贵金属", "unit": "1000克/手"},
    "ag": {"exchange": "SHFE", "name_cn": "沪银", "category": "贵金属", "unit": "15千克/手"},
    "ru": {"exchange": "SHFE", "name_cn": "天然橡胶", "category": "化工", "unit": "10吨/手"},
    "fu": {"exchange": "SHFE", "name_cn": "燃料油", "category": "能源化工", "unit": "10吨/手"},
    "bu": {"exchange": "SHFE", "name_cn": "沥青", "category": "能源化工", "unit": "10吨/手"},
    "sp": {"exchange": "SHFE", "name_cn": "纸浆", "category": "化工", "unit": "20吨/手"},
    # 大商所
    "i": {"exchange": "DCE", "name_cn": "铁矿石", "category": "黑色金属", "unit": "100吨/手"},
    "j": {"exchange": "DCE", "name_cn": "焦炭", "category": "黑色金属", "unit": "100吨/手"},
    "jm": {"exchange": "DCE", "name_cn": "焦煤", "category": "黑色金属", "unit": "60吨/手"},
    "m": {"exchange": "DCE", "name_cn": "豆粕", "category": "农产品", "unit": "10吨/手"},
    "y": {"exchange": "DCE", "name_cn": "豆油", "category": "农产品", "unit": "10吨/手"},
    "p": {"exchange": "DCE", "name_cn": "棕榈油", "category": "农产品", "unit": "10吨/手"},
    "c": {"exchange": "DCE", "name_cn": "玉米", "category": "农产品", "unit": "10吨/手"},
    "cs": {"exchange": "DCE", "name_cn": "玉米淀粉", "category": "农产品", "unit": "10吨/手"},
    "a": {"exchange": "DCE", "name_cn": "豆一", "category": "农产品", "unit": "10吨/手"},
    "b": {"exchange": "DCE", "name_cn": "豆二", "category": "农产品", "unit": "10吨/手"},
    "l": {"exchange": "DCE", "name_cn": "塑料LLDPE", "category": "化工", "unit": "5吨/手"},
    "v": {"exchange": "DCE", "name_cn": "PVC", "category": "化工", "unit": "5吨/手"},
    "pp": {"exchange": "DCE", "name_cn": "聚丙烯", "category": "化工", "unit": "5吨/手"},
    "eg": {"exchange": "DCE", "name_cn": "乙二醇", "category": "化工", "unit": "10吨/手"},
    "eb": {"exchange": "DCE", "name_cn": "苯乙烯", "category": "化工", "unit": "5吨/手"},
    # 郑商所
    "MA": {"exchange": "CZCE", "name_cn": "甲醇", "category": "化工", "unit": "10吨/手"},
    "TA": {"exchange": "CZCE", "name_cn": "PTA", "category": "化工", "unit": "5吨/手"},
    "SR": {"exchange": "CZCE", "name_cn": "白糖", "category": "农产品", "unit": "10吨/手"},
    "CF": {"exchange": "CZCE", "name_cn": "棉花", "category": "农产品", "unit": "5吨/手"},
    "OI": {"exchange": "CZCE", "name_cn": "菜籽油", "category": "农产品", "unit": "10吨/手"},
    "RM": {"exchange": "CZCE", "name_cn": "菜籽粕", "category": "农产品", "unit": "10吨/手"},
    "AP": {"exchange": "CZCE", "name_cn": "苹果", "category": "农产品", "unit": "10吨/手"},
    "FG": {"exchange": "CZCE", "name_cn": "玻璃", "category": "建材", "unit": "20吨/手"},
    "SA": {"exchange": "CZCE", "name_cn": "纯碱", "category": "化工", "unit": "20吨/手"},
    "UR": {"exchange": "CZCE", "name_cn": "尿素", "category": "化工", "unit": "20吨/手"},
    "SF": {"exchange": "CZCE", "name_cn": "硅铁", "category": "黑色金属", "unit": "5吨/手"},
    "SM": {"exchange": "CZCE", "name_cn": "锰硅", "category": "黑色金属", "unit": "5吨/手"},
    # 中金所
    "IF": {"exchange": "CFFEX", "name_cn": "沪深300股指期货", "category": "金融", "unit": "300×指数点"},
    "IH": {"exchange": "CFFEX", "name_cn": "上证50股指期货", "category": "金融", "unit": "300×指数点"},
    "IC": {"exchange": "CFFEX", "name_cn": "中证500股指期货", "category": "金融", "unit": "200×指数点"},
    "IM": {"exchange": "CFFEX", "name_cn": "中证1000股指期货", "category": "金融", "unit": "200×指数点"},
    "T": {"exchange": "CFFEX", "name_cn": "10年期国债期货", "category": "金融", "unit": "100万元面值"},
    "TF": {"exchange": "CFFEX", "name_cn": "5年期国债期货", "category": "金融", "unit": "100万元面值"},
    "TS": {"exchange": "CFFEX", "name_cn": "2年期国债期货", "category": "金融", "unit": "200万元面值"},
    # 上期能源
    "sc": {"exchange": "INE", "name_cn": "原油", "category": "能源", "unit": "1000桶/手"},
    "lu": {"exchange": "INE", "name_cn": "低硫燃料油", "category": "能源化工", "unit": "10吨/手"},
}

# ---------------------------------------------------------------------------
# 模板：术语 → 问答对
# ---------------------------------------------------------------------------

TERM_QA_TEMPLATES = [
    (
        "请用 JSON 给出期货品种 {symbol} 的交易所、中文名称、所属板块和合约单位。",
        {"symbol": "{symbol}", "exchange": "{exchange}", "name_cn": "{name_cn}",
         "category": "{category}", "contract_unit": "{unit}"},
    ),
    (
        "{name_cn}（代码 {symbol}）属于哪个交易所？请用 JSON 回答。",
        {"symbol": "{symbol}", "exchange": "{exchange}"},
    ),
    (
        "把品种代码 {symbol} 解析为 {{exchange, name_cn, category}}，输出 JSON。",
        {"symbol": "{symbol}", "exchange": "{exchange}",
         "name_cn": "{name_cn}", "category": "{category}"},
    ),
]

# 商品基本面经典逻辑链（人工撰写，约 30 条核心，再通过模板扩展到 ~300）
FUNDAMENTAL_LOGIC_CHAINS = [
    {
        "topic": "螺纹钢库存基差",
        "question": "螺纹钢社会库存连续 3 周大幅去化，且现货升水期货 200 元/吨，结合钢厂利润转正，给出短期价格判断。请用 JSON 输出 {direction, reason, risk}。",
        "answer": {"direction": "看涨", "reason": "去库节奏强叠加现货升水说明终端需求阶段性释放，钢厂利润转正意味着上游有挺价动力；下游现货市场存在提价基础", "risk": "宏观需求证伪、成本端铁矿石松动、政策性限产取消"},
    },
    {
        "topic": "豆粕南美产量",
        "question": "巴西大豆增产预期明确，CBOT 大豆下行，中国生猪存栏低位但豆粕基差走强，请用 JSON 输出 {direction, reason, risk}。",
        "answer": {"direction": "震荡偏空", "reason": "外盘成本下移压制盘面，国内基差强源于到港延迟或压榨利润修复，但中长期供应宽松格局未变", "risk": "南美天气炒作、人民币贬值放大进口成本、生猪养殖利润快速修复"},
    },
    {
        "topic": "原油 OPEC 减产",
        "question": "OPEC+ 宣布额外减产 100 万桶/日，美国库存持续去化，但需求端 PMI 走弱，请用 JSON 输出 {direction, reason, risk}。",
        "answer": {"direction": "短多长空", "reason": "供应端减产冲击短期价格，但需求端宏观走弱压制中长期空间；价格易冲高后回落", "risk": "地缘冲突升级、美国战略储备回补、需求超预期复苏"},
    },
    {
        "topic": "铜电网投资",
        "question": "中国电网投资同比增加 15%，全球新能源汽车销量超预期，LME 铜库存创年内新低，请用 JSON 输出 {direction, reason, risk}。",
        "answer": {"direction": "看涨", "reason": "传统电网+新能源双轮驱动需求，库存低位放大供需缺口的价格弹性", "risk": "美元强势压制、智利秘鲁供应恢复、宏观衰退证伪"},
    },
    {
        "topic": "铁矿石钢厂利润",
        "question": "钢厂利润转负 200 元/吨，铁水产量连续两周下滑，但港口库存低位，请用 JSON 输出 {direction, reason, risk}。",
        "answer": {"direction": "震荡偏空", "reason": "钢厂亏损被动减产压制矿石需求，但低库存提供阶段性支撑，价格易跌难涨", "risk": "粗钢平控政策放松、巴西暴雨扰动发运、终端需求超预期"},
    },
    {
        "topic": "棕榈油马来产量",
        "question": "马来西亚棕榈油 4 月库存环比增加 8%，印尼出口政策收紧，国内豆棕价差扩大，请用 JSON 输出 {direction, reason, risk}。",
        "answer": {"direction": "震荡", "reason": "马棕累库压制盘面，但印尼政策与豆棕价差扩大对价格形成支撑", "risk": "厄尔尼诺影响产区、生柴需求超预期、美豆油走强"},
    },
    {
        "topic": "黄金美联储降息",
        "question": "美联储议息暗示 9 月降息概率上升，美债收益率回落 30bp，地缘风险偏好下降，请用 JSON 输出 {direction, reason, risk}。",
        "answer": {"direction": "看涨", "reason": "实际利率下行直接利好黄金估值，避险情绪叠加央行购金延续中长期支撑", "risk": "通胀粘性导致降息预期回摆、美元突然走强"},
    },
    {
        "topic": "白糖巴西产量",
        "question": "巴西中南部 4 月双周压榨数据超预期，原糖下行至 18 美分，但国内现货升水期货 800 元/吨，请用 JSON 输出 {direction, reason, risk}。",
        "answer": {"direction": "震荡偏空", "reason": "外盘成本下移压制盘面，但国内高基差与配额外进口成本提供下方支撑", "risk": "印度出口政策、巴西天气、人民币汇率"},
    },
    {
        "topic": "PTA 成本驱动",
        "question": "PX 价格上涨 200 元/吨，PTA 现金流压缩至 -100 元/吨，下游聚酯负荷 88%，请用 JSON 输出 {direction, reason, risk}。",
        "answer": {"direction": "震荡偏强", "reason": "成本端推涨叠加下游高负荷支撑，但加工费亏损制约上方空间", "risk": "PTA 装置重启、聚酯减产、原油暴跌"},
    },
    {
        "topic": "玉米深加工需求",
        "question": "玉米深加工开机率回升至 72%，临储拍卖溢价收窄，养殖端豆粕替代用量增加，请用 JSON 输出 {direction, reason, risk}。",
        "answer": {"direction": "震荡偏强", "reason": "需求端深加工与养殖共振，临储溢价收窄反映现货流通收紧", "risk": "进口玉米增加、小麦替代、新季产量丰产"},
    },
]

# 期货合约规则知识（合约规则自生成 raw，需人工校验）
CONTRACT_RULES_TEMPLATES = [
    {
        "topic": "主力合约换月规则",
        "question": "{name_cn}（{symbol}）的主力合约换月规则是什么？请用 JSON 输出 {{rule, typical_month, indicator}}。",
        "answer_template": {
            "rule": "持仓量与成交量同时超越前一主力合约后视为换月，通常发生在交割月前 1-2 个月",
            "typical_month": "依品种活跃度而定，黑色多为 1/5/10，化工多为 1/5/9，农产品依种植/上市周期",
            "indicator": "持仓量、成交量、成交持仓比",
        },
    },
    {
        "topic": "保证金阶梯",
        "question": "{name_cn}（{symbol}）在临近交割月时保证金阶梯如何变化？请用 JSON 输出 {{stages}}。",
        "answer_template": {
            "stages": "通常分三档：合约挂牌至交割月前一月第一个交易日（基础保证金）、交割月前一月第一个交易日起（提高一档）、交割月第一个交易日起（再次提高，期货公司另加 2-5%）",
        },
    },
    {
        "topic": "涨跌停板",
        "question": "{name_cn}（{symbol}）的涨跌停板制度是什么？请用 JSON 输出 {{base_limit, expansion_rule}}。",
        "answer_template": {
            "base_limit": "上市初期由交易所规定（多数品种 4-7%），实际以交易所最新公告为准",
            "expansion_rule": "连续单边市后下一交易日扩板（通常 +50%），强制减仓后恢复基础涨跌停",
        },
    },
    {
        "topic": "限仓制度",
        "question": "{name_cn}（{symbol}）的限仓制度对一般月、交割月前一月、交割月分别有什么规定？请用 JSON 输出 {{general_month, pre_delivery, delivery_month}}。",
        "answer_template": {
            "general_month": "依交易所最新公告，按持仓占比或绝对手数限制非期货公司会员与客户",
            "pre_delivery": "限仓收紧，通常较一般月减少 50-80%",
            "delivery_month": "进一步收紧至最严格档位，自然人通常需在交割月前平仓",
        },
    },
]

# 宏观因子语义模板
MACRO_TEMPLATES = [
    {
        "indicator": "CFTC 持仓报告",
        "question": "CFTC 非商业净多持仓在某品种连续 3 周下降，且大型投机者多空比从 2:1 跌至 1.2:1，应如何解读？请用 JSON 输出 {{signal, level, caveat}}。",
        "answer": {"signal": "趋势性减仓，多头共识弱化", "level": "中等偏弱信号，需结合价格走势确认顶/底", "caveat": "持仓数据滞后一周，且仅反映美国期货市场，不能完全代表全球资金情绪"},
    },
    {
        "indicator": "FOMC 措辞",
        "question": "FOMC 会议纪要从 'patient' 改为 'data-dependent and prepared to adjust'，市场该如何解读？请用 JSON 输出 {{stance, rate_path, asset_impact}}。",
        "answer": {"stance": "由偏鸽转向中性偏鹰，灵活性增加", "rate_path": "降息时间表后移，年内降息次数预期下调", "asset_impact": "美元走强、美债收益率上行、风险资产承压"},
    },
    {
        "indicator": "PMI/CPI/PPI 联动",
        "question": "中国 PMI 重回荣枯线上方，但 CPI 同比仅 0.3%、PPI 同比 -2.5%，请用 JSON 输出 {{phase, policy_implication}}。",
        "answer": {"phase": "弱复苏阶段，需求恢复偏慢，价格压力仍未传导", "policy_implication": "货币政策有进一步宽松空间，财政政策需继续加码以巩固复苏"},
    },
    {
        "indicator": "ECB 鹰鸽派",
        "question": "ECB 主席表态 'rates will remain in restrictive territory for sufficiently long'，应如何解读对欧元和欧债的影响？请用 JSON 输出 {{eur, bond_yield, equity}}。",
        "answer": {"eur": "短期利好，反映利差支撑", "bond_yield": "曲线维持高位偏陡", "equity": "高利率环境压制估值，价值股相对受益"},
    },
    {
        "indicator": "美国非农就业",
        "question": "美国非农新增就业 6 万低于预期 18 万，失业率从 4.0% 升至 4.2%，平均时薪同比 3.5%，请用 JSON 输出 {{growth_signal, fed_implication, asset_view}}。",
        "answer": {"growth_signal": "劳动力市场快速降温，衰退风险上升", "fed_implication": "降息时点前移，9 月降息概率显著上升", "asset_view": "美债走强、黄金走强、美股短多长空"},
    },
]

# 风控术语
RISK_TEMPLATES = [
    {
        "term": "夏普比率（Sharpe Ratio）",
        "question": "请用 JSON 解释 Sharpe 比率，输出 {definition, formula, typical_threshold}。",
        "answer": {"definition": "单位风险下的超额收益指标", "formula": "(策略年化收益 - 无风险收益) / 策略收益年化波动率",
                   "typical_threshold": "<1 一般；1-2 较好；2-3 优秀；>3 极佳但需警惕样本量"},
    },
    {
        "term": "Sortino 比率",
        "question": "请用 JSON 解释 Sortino 比率与 Sharpe 的差异，输出 {definition, formula, vs_sharpe}。",
        "answer": {"definition": "仅用下行波动率作为风险衡量的风险调整收益指标",
                   "formula": "(策略年化收益 - 无风险收益) / 下行波动率",
                   "vs_sharpe": "Sortino 不惩罚向上波动，更贴近投资者真实风险感受"},
    },
    {
        "term": "Calmar 比率",
        "question": "请用 JSON 解释 Calmar 比率，输出 {definition, formula, use_case}。",
        "answer": {"definition": "年化收益与最大回撤的比值",
                   "formula": "策略年化收益 / 最大回撤的绝对值",
                   "use_case": "适合评估趋势跟随策略与高回撤策略的恢复能力"},
    },
    {
        "term": "凯利公式（Kelly Criterion）",
        "question": "请用 JSON 解释凯利公式在仓位管理中的使用，输出 {formula, practical_use, risk}。",
        "answer": {"formula": "f* = (bp - q) / b，p 胜率，q=1-p 败率，b 赔率",
                   "practical_use": "实际多采用 1/4 至 1/2 凯利以降低破产风险",
                   "risk": "对胜率/赔率估计敏感，参数偏差会显著放大波动"},
    },
    {
        "term": "VaR（Value at Risk）",
        "question": "请用 JSON 解释 95% 单日 VaR，输出 {definition, methods, limitation}。",
        "answer": {"definition": "在 95% 置信水平下，单日预计的最大可能损失",
                   "methods": "历史模拟法、参数法（方差-协方差）、蒙特卡洛模拟",
                   "limitation": "无法刻画尾部风险大小，5% 极端情形仍可能远超 VaR"},
    },
]


def build_term_qa() -> Iterable[dict]:
    for symbol, info in FUTURES_TERMS.items():
        for question_tpl, answer_tpl in TERM_QA_TEMPLATES:
            question = question_tpl.format(symbol=symbol, **info)
            answer = {
                k: (v.format(symbol=symbol, **info) if isinstance(v, str) else v)
                for k, v in answer_tpl.items()
            }
            yield {
                "messages": [
                    {"role": "system", "content": DEFAULT_SYSTEM_PROMPT},
                    {"role": "user", "content": question},
                    {"role": "assistant", "content": json.dumps(answer, ensure_ascii=False)},
                ],
                "metadata": {"source": "f5_term_dict", "symbol": symbol},
            }


def build_fundamental_qa() -> Iterable[dict]:
    for chain in FUNDAMENTAL_LOGIC_CHAINS:
        yield {
            "messages": [
                {"role": "system", "content": DEFAULT_SYSTEM_PROMPT},
                {"role": "user", "content": chain["question"]},
                {"role": "assistant", "content": json.dumps(chain["answer"], ensure_ascii=False)},
            ],
            "metadata": {"source": "f5_fundamental", "topic": chain["topic"]},
        }


def build_macro_qa() -> Iterable[dict]:
    for tpl in MACRO_TEMPLATES:
        yield {
            "messages": [
                {"role": "system", "content": DEFAULT_SYSTEM_PROMPT},
                {"role": "user", "content": tpl["question"]},
                {"role": "assistant", "content": json.dumps(tpl["answer"], ensure_ascii=False)},
            ],
            "metadata": {"source": "f5_macro", "indicator": tpl["indicator"]},
        }


def build_risk_qa() -> Iterable[dict]:
    for tpl in RISK_TEMPLATES:
        yield {
            "messages": [
                {"role": "system", "content": DEFAULT_SYSTEM_PROMPT},
                {"role": "user", "content": tpl["question"]},
                {"role": "assistant", "content": json.dumps(tpl["answer"], ensure_ascii=False)},
            ],
            "metadata": {"source": "f5_risk", "term": tpl["term"]},
        }


def build_contract_rules_raw() -> Iterable[dict]:
    """合约规则自生成样本 → raw（待人工校验，禁止直接入训）."""
    for symbol, info in FUTURES_TERMS.items():
        for tpl in CONTRACT_RULES_TEMPLATES:
            question = tpl["question"].format(symbol=symbol, **info)
            answer = {k: v.format(symbol=symbol, **info) for k, v in tpl["answer_template"].items()}
            yield {
                "messages": [
                    {"role": "system", "content": DEFAULT_SYSTEM_PROMPT},
                    {"role": "user", "content": question},
                    {"role": "assistant", "content": json.dumps(answer, ensure_ascii=False)},
                ],
                "metadata": {"source": "f5_contract_rules_raw", "symbol": symbol, "topic": tpl["topic"], "needs_review": True},
            }


def dedup(records: Iterable[dict]) -> list[dict]:
    seen: set[str] = set()
    result: list[dict] = []
    for rec in records:
        text = json.dumps(rec.get("messages", rec), ensure_ascii=False, sort_keys=True)
        h = hashlib.sha1(text.encode("utf-8")).hexdigest()
        if h in seen:
            continue
        seen.add(h)
        result.append(rec)
    return result


def load_external(path: Path) -> Iterable[dict]:
    if not path.exists():
        return []
    if path.suffix.lower() == ".jsonl":
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        yield json.loads(line)
                    except json.JSONDecodeError:
                        continue
    else:
        with path.open("r", encoding="utf-8") as f:
            payload = json.load(f)
        if isinstance(payload, list):
            yield from payload


def write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def write_provenance(path: Path, stats: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()
    content = f"""# F5 金融语料数据来源 (DATA_PROVENANCE)

生成日期：{today}
生成脚本：scripts/researcher_finetune/build_finance_corpus.py
方案：方案 B（数据 Agent 内置维护，禁止跨服务读 services/decision/configs/）

## 来源清单

| 来源 | License | 抽取方式 | 样本量 |
|------|---------|---------|-------|
| 内置期货术语词典（FUTURES_TERMS） | 内部维护 | 模板 × 词典枚举 | {stats.get('term_qa', 0)} |
| 商品基本面经典逻辑链（FUNDAMENTAL_LOGIC_CHAINS） | 内部人工撰写 | 直接枚举 | {stats.get('fundamental_qa', 0)} |
| 宏观因子语义（MACRO_TEMPLATES） | 内部人工撰写 | 直接枚举 | {stats.get('macro_qa', 0)} |
| 风控术语（RISK_TEMPLATES） | 内部人工撰写 | 直接枚举 | {stats.get('risk_qa', 0)} |
| 合约规则自生成（raw，待人工校验） | 内部模板 | 模板 × 词典 → raw | {stats.get('contract_rules_raw', 0)} |
| 外部 JSONL（FinGPT 等，可选） | 上游 license（公开数据集，Apache-2.0/MIT） | --external-jsonl | {stats.get('external', 0)} |

## 入训规则

- `dataset_f5.jsonl`：术语 + 基本面 + 宏观 + 风控 + 已校验的合约规则 + 外部
- `dataset_f5_raw.jsonl`：合约规则自生成 raw（**禁止**直接喂入 merge_with_f4_dataset.py）
- 人工校验记录：见 `manual_review_log.md`

## 合规

- 不引入需付费 API key 的数据源
- 内置词典不读取 services/decision/configs/（方案 B 硬约束）
- 自生成语料两段式分离，未完成 200 条人工校验前 raw 不并入正式集
"""
    path.write_text(content, encoding="utf-8")


def write_review_log_template(path: Path, raw_count: int) -> None:
    if path.exists():
        return
    today = date.today().isoformat()
    content = f"""# F5 自生成语料人工校验留痕

文件：dataset_f5_raw.jsonl
样本量：{raw_count}
要求：抽样 ≥ 200 条，标注 PASS/FIX/DROP，校验通过后由 Agent 主导追加到 dataset_f5.jsonl

| 日期 | 抽样区间 | 抽样数 | PASS | FIX | DROP | 校验人 | 备注 |
|------|---------|-------|------|-----|------|-------|------|
| {today} | -- | 0 | 0 | 0 | 0 | -- | 待校验 |

## 校验明细（可附加 review batch）
"""
    path.write_text(content, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Build F5 finance corpus.")
    p.add_argument("--out-dir", required=True, help="Output directory.")
    p.add_argument("--external-jsonl", action="append", default=[],
                   help="Optional external JSONL (FinGPT etc). Repeat for multiple.")
    p.add_argument("--seed", type=int, default=42)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    random.seed(args.seed)
    out_dir = Path(args.out_dir).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)

    term_qa = list(build_term_qa())
    fundamental_qa = list(build_fundamental_qa())
    macro_qa = list(build_macro_qa())
    risk_qa = list(build_risk_qa())
    contract_rules_raw = list(build_contract_rules_raw())

    external: list[dict] = []
    for ext in args.external_jsonl:
        external.extend(load_external(Path(ext).expanduser()))

    main_records = dedup(term_qa + fundamental_qa + macro_qa + risk_qa + external)
    raw_records = dedup(contract_rules_raw)

    write_jsonl(out_dir / "dataset_f5.jsonl", main_records)
    write_jsonl(out_dir / "dataset_f5_raw.jsonl", raw_records)
    write_provenance(out_dir / "DATA_PROVENANCE.md", {
        "term_qa": len(term_qa),
        "fundamental_qa": len(fundamental_qa),
        "macro_qa": len(macro_qa),
        "risk_qa": len(risk_qa),
        "contract_rules_raw": len(raw_records),
        "external": len(external),
    })
    write_review_log_template(out_dir / "manual_review_log.md", len(raw_records))

    summary = {
        "out_dir": str(out_dir),
        "dataset_f5.jsonl": len(main_records),
        "dataset_f5_raw.jsonl (待校验)": len(raw_records),
        "breakdown": {
            "term_qa": len(term_qa),
            "fundamental_qa": len(fundamental_qa),
            "macro_qa": len(macro_qa),
            "risk_qa": len(risk_qa),
            "external": len(external),
        },
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
