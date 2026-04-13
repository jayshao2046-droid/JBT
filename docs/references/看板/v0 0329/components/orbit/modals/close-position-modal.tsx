"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { AlertTriangle, Loader2, X, XCircle, TrendingDown, TrendingUp } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export interface PositionData {
  code: string;
  name?: string;
  direction: "long" | "short";
  quantity: number;
  avgCost: number;
  currentPrice: number;
  pnl: number;
  pnlPercent: number;
}

interface ClosePositionModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (quantity: number) => void | Promise<void>;
  position: PositionData | null;
  mode: "single" | "all";
  positions?: PositionData[];
}

export function ClosePositionModal({
  isOpen,
  onClose,
  onConfirm,
  position,
  mode,
  positions = [],
}: ClosePositionModalProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [closeQuantity, setCloseQuantity] = useState(position?.quantity || 0);

  const handleConfirm = async () => {
    setIsLoading(true);
    try {
      await onConfirm(closeQuantity);
      onClose();
    } finally {
      setIsLoading(false);
    }
  };

  // 一键平仓模式
  if (mode === "all") {
    const totalPnl = positions.reduce((sum, p) => sum + p.pnl, 0);
    const totalPositions = positions.length;
    const profitPositions = positions.filter((p) => p.pnl > 0).length;
    const lossPositions = positions.filter((p) => p.pnl < 0).length;

    return (
      <AnimatePresence>
        {isOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="absolute inset-0 bg-black/50"
              onClick={onClose}
            />

            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 10 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 10 }}
              transition={{ duration: 0.2 }}
              className="relative w-full max-w-md mx-4 bg-background border border-border rounded-xl shadow-2xl overflow-hidden"
            >
              {/* Header */}
              <div className="flex items-center justify-between px-5 py-4 border-b border-border">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-[#EF4444]/10 flex items-center justify-center">
                    <XCircle className="w-5 h-5 text-[#EF4444]" />
                  </div>
                  <div>
                    <h2 className="text-base font-semibold text-foreground">一键平仓确认</h2>
                    <p className="text-[11px] text-muted-foreground">
                      将平掉所有 {totalPositions} 个持仓
                    </p>
                  </div>
                </div>
                <button
                  onClick={onClose}
                  className="w-8 h-8 rounded-lg flex items-center justify-center hover:bg-muted transition-colors"
                >
                  <X className="w-4 h-4 text-muted-foreground" />
                </button>
              </div>

              {/* Content */}
              <div className="p-5 space-y-4">
                {/* 汇总信息 */}
                <div className="grid grid-cols-3 gap-3">
                  <div className="p-3 bg-muted/30 rounded-lg text-center">
                    <p className="text-[10px] text-muted-foreground mb-1">总持仓</p>
                    <p className="text-[15px] font-mono font-bold text-foreground">{totalPositions}</p>
                  </div>
                  <div className="p-3 bg-[#EF4444]/5 rounded-lg text-center">
                    <p className="text-[10px] text-muted-foreground mb-1">盈利持仓</p>
                    <p className="text-[15px] font-mono font-bold text-[#EF4444]">{profitPositions}</p>
                  </div>
                  <div className="p-3 bg-[#22C55E]/5 rounded-lg text-center">
                    <p className="text-[10px] text-muted-foreground mb-1">亏损持仓</p>
                    <p className="text-[15px] font-mono font-bold text-[#22C55E]">{lossPositions}</p>
                  </div>
                </div>

                {/* 预估盈亏 */}
                <div className="p-4 bg-muted/30 rounded-lg">
                  <div className="flex items-center justify-between">
                    <span className="text-[12px] text-muted-foreground">预估平仓盈亏</span>
                    <span
                      className={cn(
                        "text-[18px] font-mono font-bold",
                        totalPnl >= 0 ? "text-[#EF4444]" : "text-[#22C55E]"
                      )}
                    >
                      {totalPnl >= 0 ? "+" : ""}
                      {totalPnl.toLocaleString()}
                    </span>
                  </div>
                </div>

                {/* 持仓列表预览 */}
                <div className="max-h-[200px] overflow-y-auto space-y-1.5">
                  {positions.map((p, idx) => (
                    <div
                      key={idx}
                      className="flex items-center justify-between px-3 py-2 bg-secondary/30 rounded-md"
                    >
                      <div className="flex items-center gap-2">
                        <span className="text-[11px] font-mono font-semibold text-foreground">
                          {p.code}
                        </span>
                        <span
                          className={cn(
                            "text-[9px] px-1.5 py-0.5 rounded",
                            p.direction === "long"
                              ? "bg-[#EF4444]/10 text-[#EF4444]"
                              : "bg-[#22C55E]/10 text-[#22C55E]"
                          )}
                        >
                          {p.direction === "long" ? "多" : "空"}
                        </span>
                      </div>
                      <span
                        className={cn(
                          "text-[11px] font-mono font-medium",
                          p.pnl >= 0 ? "text-[#EF4444]" : "text-[#22C55E]"
                        )}
                      >
                        {p.pnl >= 0 ? "+" : ""}
                        {p.pnl.toLocaleString()}
                      </span>
                    </div>
                  ))}
                </div>

                {/* 风险提示 */}
                <div className="flex items-start gap-2 p-3 bg-[#EF4444]/5 border border-[#EF4444]/20 rounded-lg">
                  <AlertTriangle className="w-4 h-4 text-[#EF4444] flex-shrink-0 mt-0.5" />
                  <p className="text-[10px] text-[#EF4444]/80 leading-relaxed">
                    此操作将平掉所有持仓，请确认您已了解市场风险。此操作不可撤销。
                  </p>
                </div>
              </div>

              {/* Footer */}
              <div className="flex items-center justify-end gap-3 px-5 py-4 border-t border-border bg-muted/20">
                <Button variant="outline" size="sm" onClick={onClose} disabled={isLoading}>
                  取消
                </Button>
                <Button
                  size="sm"
                  variant="destructive"
                  onClick={handleConfirm}
                  disabled={isLoading}
                >
                  {isLoading ? (
                    <>
                      <Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin" />
                      处理中...
                    </>
                  ) : (
                    <>确认一键平仓</>
                  )}
                </Button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    );
  }

  // 单个平仓模式
  if (!position) return null;

  const isProfit = position.pnl >= 0;
  const estimatedPnl = ((position.currentPrice - position.avgCost) * closeQuantity * (position.direction === "long" ? 1 : -1));

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 bg-black/50"
            onClick={onClose}
          />

          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 10 }}
            transition={{ duration: 0.2 }}
            className="relative w-full max-w-md mx-4 bg-background border border-border rounded-xl shadow-2xl overflow-hidden"
          >
            {/* Header */}
            <div className="flex items-center justify-between px-5 py-4 border-b border-border">
              <div className="flex items-center gap-3">
                <div
                  className={cn(
                    "w-10 h-10 rounded-lg flex items-center justify-center",
                    position.direction === "long" ? "bg-[#EF4444]/10" : "bg-[#22C55E]/10"
                  )}
                >
                  {position.direction === "long" ? (
                    <TrendingUp className="w-5 h-5 text-[#EF4444]" />
                  ) : (
                    <TrendingDown className="w-5 h-5 text-[#22C55E]" />
                  )}
                </div>
                <div>
                  <h2 className="text-base font-semibold text-foreground">平仓确认</h2>
                  <p className="text-[11px] text-muted-foreground">
                    {position.code} {position.name && `· ${position.name}`}
                  </p>
                </div>
              </div>
              <button
                onClick={onClose}
                className="w-8 h-8 rounded-lg flex items-center justify-center hover:bg-muted transition-colors"
              >
                <X className="w-4 h-4 text-muted-foreground" />
              </button>
            </div>

            {/* Content */}
            <div className="p-5 space-y-4">
              {/* 持仓信息 */}
              <div className="p-3 bg-muted/30 rounded-lg space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-[11px] text-muted-foreground">持仓方向</span>
                  <span
                    className={cn(
                      "text-[12px] font-medium px-2 py-0.5 rounded",
                      position.direction === "long"
                        ? "bg-[#EF4444]/10 text-[#EF4444]"
                        : "bg-[#22C55E]/10 text-[#22C55E]"
                    )}
                  >
                    {position.direction === "long" ? "多头" : "空头"}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-[11px] text-muted-foreground">持仓数量</span>
                  <span className="text-[13px] font-mono font-semibold text-foreground">
                    {position.quantity} 手
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-[11px] text-muted-foreground">开仓均价</span>
                  <span className="text-[13px] font-mono font-semibold text-foreground">
                    {position.avgCost.toLocaleString()}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-[11px] text-muted-foreground">当前价格</span>
                  <span className="text-[13px] font-mono font-semibold text-foreground">
                    {position.currentPrice.toLocaleString()}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-[11px] text-muted-foreground">浮动盈亏</span>
                  <span
                    className={cn(
                      "text-[13px] font-mono font-semibold",
                      isProfit ? "text-[#EF4444]" : "text-[#22C55E]"
                    )}
                  >
                    {isProfit ? "+" : ""}
                    {position.pnl.toLocaleString()} ({position.pnlPercent.toFixed(2)}%)
                  </span>
                </div>
              </div>

              {/* 平仓数量 */}
              <div>
                <label className="text-[11px] font-medium text-muted-foreground mb-1.5 block">
                  平仓数量（手）
                </label>
                <div className="flex items-center gap-2">
                  <Input
                    type="number"
                    value={closeQuantity}
                    onChange={(e) => setCloseQuantity(Math.min(Number(e.target.value), position.quantity))}
                    className="h-9 text-[13px] font-mono flex-1"
                    min={1}
                    max={position.quantity}
                  />
                  <Button
                    variant="outline"
                    size="sm"
                    className="h-9 text-[11px]"
                    onClick={() => setCloseQuantity(position.quantity)}
                  >
                    全部
                  </Button>
                </div>
              </div>

              {/* 预估盈亏 */}
              <div className="p-3 bg-muted/30 rounded-lg">
                <div className="flex items-center justify-between">
                  <span className="text-[11px] text-muted-foreground">预估平仓盈亏</span>
                  <span
                    className={cn(
                      "text-[15px] font-mono font-bold",
                      estimatedPnl >= 0 ? "text-[#EF4444]" : "text-[#22C55E]"
                    )}
                  >
                    {estimatedPnl >= 0 ? "+" : ""}
                    {estimatedPnl.toLocaleString()}
                  </span>
                </div>
              </div>
            </div>

            {/* 底部汇总行 */}
            <div className="px-5 py-3 border-t border-border bg-muted/10">
              <div className="flex items-center justify-between flex-wrap gap-x-4 gap-y-1">
                <span className="text-[10px] text-muted-foreground">
                  总持仓 <span className="font-mono font-semibold text-foreground">100</span> 手
                </span>
                <span className="text-[10px] text-muted-foreground">
                  总浮盈{" "}
                  <span className="font-mono font-semibold text-[#EF4444]">5,000</span>
                </span>
                <span className="text-[10px] text-muted-foreground">
                  保证金占用{" "}
                  <span className="font-mono font-semibold text-foreground">120,000</span>
                </span>
                <span className="text-[10px] text-muted-foreground">
                  手续费{" "}
                  <span className="font-mono font-semibold text-foreground">300</span>
                </span>
                <span className="text-[10px] text-muted-foreground">
                  滑点{" "}
                  <span className="font-mono font-semibold text-foreground">100</span>
                </span>
              </div>
            </div>

            {/* Footer */}
            <div className="flex items-center justify-end gap-3 px-5 py-4 border-t border-border bg-muted/20">
              <Button variant="outline" size="sm" onClick={onClose} disabled={isLoading}>
                取消
              </Button>
              <Button
                size="sm"
                onClick={handleConfirm}
                disabled={isLoading}
                className={cn(
                  isProfit
                    ? "bg-[#EF4444] hover:bg-[#EF4444]/90"
                    : "bg-[#22C55E] hover:bg-[#22C55E]/90"
                )}
              >
                {isLoading ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin" />
                    处理中...
                  </>
                ) : (
                  <>确认平仓</>
                )}
              </Button>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}
