// 全量期货合约定义（主连品种）
// 交易所：SHFE 上期所 / DCE 大商所 / CZCE 郑商所 / CFFEX 中金所 / INE 能源所 / GFEX 广期所

export type Sector =
  | "黑色系"
  | "有色金属"
  | "贵金属"
  | "油脂油料"
  | "农产品"
  | "化工"
  | "能源化工"
  | "软商品"
  | "金融"
  | "新能源"

export type Exchange = "SHFE" | "DCE" | "CZCE" | "CFFEX" | "INE" | "GFEX"

export interface FuturesContract {
  symbol: string      // 合约代码
  name: string        // 合约名称
  exchange: Exchange
  sector: Sector
  basePrice: number   // 参考基准价
  tick: number        // 最小变动单位
  unit: string        // 价格单位
}

export const ALL_CONTRACTS: FuturesContract[] = [
  // ── SHFE 上期所 ────────────────────────────────────────────────────────────────
  // 黑色系
  { symbol: "rbM",  name: "螺纹钢主连",     exchange: "SHFE", sector: "黑色系",   basePrice: 3097,    tick: 1,     unit: "元/吨" },
  { symbol: "hcM",  name: "热卷主连",       exchange: "SHFE", sector: "黑色系",   basePrice: 3285,    tick: 1,     unit: "元/吨" },
  { symbol: "ssM",  name: "不锈钢主连",     exchange: "SHFE", sector: "黑色系",   basePrice: 13095,   tick: 5,     unit: "元/吨" },
  { symbol: "spM",  name: "纸浆主连",       exchange: "SHFE", sector: "化工",     basePrice: 5700,    tick: 2,     unit: "元/吨" },
  // 有色金属
  { symbol: "cuM",  name: "沪铜主连",       exchange: "SHFE", sector: "有色金属", basePrice: 77000,   tick: 10,    unit: "元/吨" },
  { symbol: "alM",  name: "沪铝主连",       exchange: "SHFE", sector: "有色金属", basePrice: 20000,   tick: 5,     unit: "元/吨" },
  { symbol: "znM",  name: "沪锌主连",       exchange: "SHFE", sector: "有色金属", basePrice: 22500,   tick: 5,     unit: "元/吨" },
  { symbol: "pbM",  name: "沪铅主连",       exchange: "SHFE", sector: "有色金属", basePrice: 16800,   tick: 5,     unit: "元/吨" },
  { symbol: "niM",  name: "沪镍主连",       exchange: "SHFE", sector: "有色金属", basePrice: 120000,  tick: 10,    unit: "元/吨" },
  { symbol: "snM",  name: "沪锡主连",       exchange: "SHFE", sector: "有色金属", basePrice: 260000,  tick: 10,    unit: "元/吨" },
  { symbol: "bcM",  name: "国际铜主连",     exchange: "SHFE", sector: "有色金属", basePrice: 62000,   tick: 10,    unit: "美元/吨" },
  // 贵金属
  { symbol: "auM",  name: "沪金主连",       exchange: "SHFE", sector: "贵金属",   basePrice: 745,     tick: 0.02,  unit: "元/克" },
  { symbol: "agM",  name: "沪银主连",       exchange: "SHFE", sector: "贵金属",   basePrice: 8200,    tick: 1,     unit: "元/千克" },
  // 能源化工
  { symbol: "fuM",  name: "燃料油主连",     exchange: "SHFE", sector: "能源化工", basePrice: 3750,    tick: 1,     unit: "元/吨" },
  { symbol: "buM",  name: "沥青主连",       exchange: "SHFE", sector: "能源化工", basePrice: 4300,    tick: 2,     unit: "元/吨" },
  { symbol: "ruM",  name: "天然橡胶主连",   exchange: "SHFE", sector: "化工",     basePrice: 16845,   tick: 5,     unit: "元/吨" },
  { symbol: "nrM",  name: "20号胶主连",     exchange: "SHFE", sector: "化工",     basePrice: 13800,   tick: 5,     unit: "元/吨" },

  // ── DCE 大商所 ────────────────────────────────────────────────────────────────
  // 黑色系
  { symbol: "iM",   name: "铁矿石主连",     exchange: "DCE",  sector: "黑色系",   basePrice: 799.5,   tick: 0.5,   unit: "元/吨" },
  { symbol: "jM",   name: "焦炭主连",       exchange: "DCE",  sector: "黑色系",   basePrice: 1670,    tick: 0.5,   unit: "元/吨" },
  { symbol: "jmM",  name: "焦煤主连",       exchange: "DCE",  sector: "黑色系",   basePrice: 1112.5,  tick: 0.5,   unit: "元/吨" },
  // 油脂油料
  { symbol: "aM",   name: "大豆一号主连",   exchange: "DCE",  sector: "油脂油料", basePrice: 4280,    tick: 1,     unit: "元/吨" },
  { symbol: "bM",   name: "大豆二号主连",   exchange: "DCE",  sector: "油脂油料", basePrice: 3530,    tick: 1,     unit: "元/吨" },
  { symbol: "mM",   name: "豆粕主连",       exchange: "DCE",  sector: "油脂油料", basePrice: 2843,    tick: 1,     unit: "元/吨" },
  { symbol: "yM",   name: "豆油主连",       exchange: "DCE",  sector: "油脂油料", basePrice: 8694,    tick: 2,     unit: "元/吨" },
  { symbol: "pM",   name: "棕榈油主连",     exchange: "DCE",  sector: "油脂油料", basePrice: 9938,    tick: 2,     unit: "元/吨" },
  // 农产品
  { symbol: "cM",   name: "玉米主连",       exchange: "DCE",  sector: "农产品",   basePrice: 2344,    tick: 1,     unit: "元/吨" },
  { symbol: "csM",  name: "玉米淀粉主连",   exchange: "DCE",  sector: "农产品",   basePrice: 2680,    tick: 1,     unit: "元/吨" },
  { symbol: "rrM",  name: "粳米主连",       exchange: "DCE",  sector: "农产品",   basePrice: 3570,    tick: 1,     unit: "元/吨" },
  { symbol: "lhM",  name: "生猪主连",       exchange: "DCE",  sector: "农产品",   basePrice: 15400,   tick: 5,     unit: "元/吨" },
  // 化工
  { symbol: "vM",   name: "PVC主连",        exchange: "DCE",  sector: "化工",     basePrice: 5428,    tick: 2,     unit: "元/吨" },
  { symbol: "lM",   name: "塑料主连",       exchange: "DCE",  sector: "化工",     basePrice: 8799,    tick: 5,     unit: "元/吨" },
  { symbol: "ppM",  name: "聚丙烯主连",     exchange: "DCE",  sector: "化工",     basePrice: 7300,    tick: 1,     unit: "元/吨" },
  { symbol: "egM",  name: "乙二醇主连",     exchange: "DCE",  sector: "化工",     basePrice: 4480,    tick: 1,     unit: "元/吨" },
  { symbol: "ebM",  name: "苯乙烯主连",     exchange: "DCE",  sector: "化工",     basePrice: 9850,    tick: 1,     unit: "元/吨" },
  { symbol: "pgM",  name: "液化气主连",     exchange: "DCE",  sector: "能源化工", basePrice: 4550,    tick: 2,     unit: "元/吨" },

  // ── CZCE 郑商所 ───────────────────────────────────────────────────────────────
  // 软商品
  { symbol: "CFM",  name: "棉花主连",       exchange: "CZCE", sector: "软商品",   basePrice: 15255,   tick: 5,     unit: "元/吨" },
  { symbol: "CYM",  name: "棉纱主连",       exchange: "CZCE", sector: "软商品",   basePrice: 13450,   tick: 5,     unit: "元/吨" },
  // 农产品
  { symbol: "SRM",  name: "白糖主连",       exchange: "CZCE", sector: "农产品",   basePrice: 5480,    tick: 1,     unit: "元/吨" },
  { symbol: "APM",  name: "苹果主连",       exchange: "CZCE", sector: "农产品",   basePrice: 6450,    tick: 2,     unit: "元/吨" },
  { symbol: "CJM",  name: "红枣主连",       exchange: "CZCE", sector: "农产品",   basePrice: 9800,    tick: 5,     unit: "元/吨" },
  // 油脂油料
  { symbol: "OIM",  name: "菜油主连",       exchange: "CZCE", sector: "油脂油料", basePrice: 9765,    tick: 2,     unit: "元/吨" },
  { symbol: "RMM",  name: "菜粕主连",       exchange: "CZCE", sector: "油脂油料", basePrice: 2680,    tick: 1,     unit: "元/吨" },
  { symbol: "RSM",  name: "油菜籽主连",     exchange: "CZCE", sector: "油脂油料", basePrice: 6450,    tick: 1,     unit: "元/吨" },
  { symbol: "PKM",  name: "花生主连",       exchange: "CZCE", sector: "油脂油料", basePrice: 8780,    tick: 2,     unit: "元/吨" },
  // 黑色系
  { symbol: "SMM",  name: "锰硅主连",       exchange: "CZCE", sector: "黑色系",   basePrice: 6480,    tick: 2,     unit: "元/吨" },
  { symbol: "SFM",  name: "硅铁主连",       exchange: "CZCE", sector: "黑色系",   basePrice: 6160,    tick: 2,     unit: "元/吨" },
  // 化工
  { symbol: "TAM",  name: "PTA主连",        exchange: "CZCE", sector: "化工",     basePrice: 6988,    tick: 2,     unit: "元/吨" },
  { symbol: "MAM",  name: "甲醇主连",       exchange: "CZCE", sector: "化工",     basePrice: 3364,    tick: 1,     unit: "元/吨" },
  { symbol: "FGM",  name: "玻璃主连",       exchange: "CZCE", sector: "化工",     basePrice: 1450,    tick: 1,     unit: "元/吨" },
  { symbol: "SAM",  name: "纯碱主连",       exchange: "CZCE", sector: "化工",     basePrice: 1740,    tick: 1,     unit: "元/吨" },
  { symbol: "URM",  name: "尿素主连",       exchange: "CZCE", sector: "化工",     basePrice: 1785,    tick: 1,     unit: "元/吨" },
  { symbol: "PFM",  name: "短纤主连",       exchange: "CZCE", sector: "化工",     basePrice: 6800,    tick: 2,     unit: "元/吨" },
  { symbol: "PXM",  name: "对二甲苯主连",   exchange: "CZCE", sector: "化工",     basePrice: 7450,    tick: 2,     unit: "元/吨" },

  // ── CFFEX 中金所 ──────────────────────────────────────────────────────────────
  { symbol: "IF",   name: "沪深300主力",    exchange: "CFFEX",sector: "金融",     basePrice: 3950,    tick: 0.2,   unit: "点" },
  { symbol: "IC",   name: "中证500主力",    exchange: "CFFEX",sector: "金融",     basePrice: 5500,    tick: 0.2,   unit: "点" },
  { symbol: "IH",   name: "上证50主力",     exchange: "CFFEX",sector: "金融",     basePrice: 2640,    tick: 0.2,   unit: "点" },
  { symbol: "IM",   name: "中证1000主力",   exchange: "CFFEX",sector: "金融",     basePrice: 5870,    tick: 0.2,   unit: "点" },
  { symbol: "T",    name: "10年国债主力",   exchange: "CFFEX",sector: "金融",     basePrice: 105.45,  tick: 0.005, unit: "元" },
  { symbol: "TF",   name: "5年国债主力",    exchange: "CFFEX",sector: "金融",     basePrice: 103.22,  tick: 0.005, unit: "元" },
  { symbol: "TS",   name: "2年国债主力",    exchange: "CFFEX",sector: "金融",     basePrice: 101.55,  tick: 0.005, unit: "元" },
  { symbol: "TL",   name: "30年国债主力",   exchange: "CFFEX",sector: "金融",     basePrice: 116.20,  tick: 0.005, unit: "元" },

  // ── INE 上海能源 ───────────────────────────────────────────────────────────────
  { symbol: "scM",  name: "原油主连",       exchange: "INE",  sector: "能源化工", basePrice: 535,     tick: 0.1,   unit: "元/桶" },
  { symbol: "luM",  name: "低硫燃料油主连", exchange: "INE",  sector: "能源化工", basePrice: 3780,    tick: 1,     unit: "元/吨" },

  // ── GFEX 广期所 ───────────────────────────────────────────────────────────────
  { symbol: "siM",  name: "工业硅主连",     exchange: "GFEX", sector: "新能源",   basePrice: 11500,   tick: 5,     unit: "元/吨" },
  { symbol: "lcM",  name: "碳酸锂主连",     exchange: "GFEX", sector: "新能源",   basePrice: 64000,   tick: 50,    unit: "元/吨" },
]

// 自选列表预设（5 组）
export const WATCHLISTS = [
  {
    id: 1,
    name: "全部合约",
    symbols: ALL_CONTRACTS.map(c => c.symbol),
  },
  {
    id: 2,
    name: "黑色系",
    symbols: ["rbM", "hcM", "ssM", "iM", "jM", "jmM", "SMM", "SFM"],
  },
  {
    id: 3,
    name: "油脂",
    symbols: ["pM", "OIM", "PKM", "yM", "mM", "aM", "bM", "RMM", "RSM"],
  },
  {
    id: 4,
    name: "农产品",
    symbols: ["cM", "csM", "SRM", "CFM", "APM", "CJM", "rrM", "lhM"],
  },
  {
    id: 5,
    name: "化工",
    symbols: ["TAM", "MAM", "vM", "lM", "ppM", "egM", "buM", "fuM", "ruM", "pgM", "ebM", "PFM", "SAM", "URM", "spM", "nrM", "scM", "luM", "siM", "lcM"],
  },
]

/** 根据 tick 决定小数位数 */
export function getDecimals(tick: number): number {
  if (tick >= 1) return 0
  const s = tick.toString()
  const dotIdx = s.indexOf(".")
  return dotIdx === -1 ? 0 : s.length - dotIdx - 1
}

/** 格式化价格 */
export function fmtPrice(price: number, tick: number): string {
  return price.toFixed(getDecimals(tick))
}
