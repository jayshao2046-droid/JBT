"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { TrendingUp, TrendingDown, Loader2, AlertTriangle, X } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export interface SignalData {
  code: string;
  name?: string;
  currentPrice: number;
  signal: "买入" | "卖出" | "观望";
  confidence: number;
  type: "buy" | "sell" | "hold";
  suggestedQuantity?: number;
  stopLoss?: number;
  takeProfit?: number;
  reason?: string;
}

interface SignalConfirmModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (quantity: number, stopLoss: number, takeProfit: number) => void | Promise<void>;
  signal: SignalData | null;
}

export function SignalConfirmModal({
  isOpen,
  onClose,
  onConfirm,
  signal,
}: SignalConfirmModalProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [quantity, setQuantity] = useState(signal?.suggestedQuantity || 1);
  const [stopLoss, setStopLoss] = useState(signal?.stopLoss || 0);
  const [takeProfit, setTakeProfit] = useState(signal?.takeProfit || 0);

  const handleConfirm = async () => {
    setIsLoading(true);
    try {
      await onConfirm(quantity, stopLoss, takeProfit);
      onClose();
    } finally {
      setIsLoading(false);
    }
  };

  if (!signal) return null;

  const isBuy = signal.type === "buy";
  const totalAmount = signal.currentPrice * quantity;

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 bg-black/50"
            onClick={onClose}
          />

          {/* Modal */}
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
                    isBuy ? "bg-[#EF4444]/10" : "bg-[#22C55E]/10"
                  )}
                >
                  {isBuy ? (
                    <TrendingUp className="w-5 h-5 text-[#EF4444]" />
                  ) : (
                    <TrendingDown className="w-5 h-5 text-[#22C55E]" />
                  )}
                </div>
                <div>
                  <h2 className="text-base font-semibold text-foreground">
                    确认{signal.signal}信号
                  </h2>
                  <p className="text-[11px] text-muted-foreground">
                    {signal.code} {signal.name && `· ${signal.name}`}
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
              {/* 信号信息 */}
              <div className="p-3 bg-muted/30 rounded-lg space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-[11px] text-muted-foreground">当前价格</span>
                  <span className="text-[13px] font-mono font-semibold text-foreground">
                    {signal.currentPrice.toLocaleString()}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-[11px] text-muted-foreground">信号置信度</span>
                  <span
                    className={cn(
                      "text-[13px] font-mono font-semibold",
                      signal.confidence >= 80
                        ? "text-[#22C55E]"
                        : signal.confidence >= 60
                        ? "text-warning"
                        : "text-muted-foreground"
                    )}
                  >
                    {signal.confidence}%
                  </span>
                </div>
                {signal.reason && (
                  <div className="pt-2 border-t border-border/50">
                    <span className="text-[10px] text-muted-foreground/70">
                      信号原因：{signal.reason}
                    </span>
                  </div>
                )}
              </div>

              {/* 交易参数 */}
              <div className="space-y-3">
                <div>
                  <label className="text-[11px] font-medium text-muted-foreground mb-1.5 block">
                    交易数量（手）
                  </label>
                  <Input
                    type="number"
                    value={quantity}
                    onChange={(e) => setQuantity(Number(e.target.value))}
                    className="h-9 text-[13px] font-mono"
                    min={1}
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-[11px] font-medium text-muted-foreground mb-1.5 block">
                      止损价
                    </label>
                    <Input
                      type="number"
                      value={stopLoss}
                      onChange={(e) => setStopLoss(Number(e.target.value))}
                      className="h-9 text-[13px] font-mono"
                      placeholder="可选"
                    />
                  </div>
                  <div>
                    <label className="text-[11px] font-medium text-muted-foreground mb-1.5 block">
                      止盈价
                    </label>
                    <Input
                      type="number"
                      value={takeProfit}
                      onChange={(e) => setTakeProfit(Number(e.target.value))}
                      className="h-9 text-[13px] font-mono"
                      placeholder="可选"
                    />
                  </div>
                </div>

                {/* 预估金额 */}
                <div className="p-3 bg-muted/30 rounded-lg">
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] text-muted-foreground">预估交易金额</span>
                    <span className="text-[15px] font-mono font-bold text-foreground">
                      {totalAmount.toLocaleString()}
                    </span>
                  </div>
                </div>
              </div>

              {/* 风险提示 */}
              <div className="flex items-start gap-2 p-3 bg-warning/5 border border-warning/20 rounded-lg">
                <AlertTriangle className="w-4 h-4 text-warning flex-shrink-0 mt-0.5" />
                <p className="text-[10px] text-warning/80 leading-relaxed">
                  交易有风险，请确认您已了解相关风险并愿意承担。建议设置止损止盈以控制风险。
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
                onClick={handleConfirm}
                disabled={isLoading}
                className={cn(
                  isBuy
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
                  <>确认{signal.signal}</>
                )}
              </Button>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}
