"use client";

import { useState, useMemo } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";
import { CheckCircle2, XCircle, Loader2, Search } from "lucide-react";

// 期货品种数据
const futuresContracts = [
  { code: "RB2406", name: "螺纹钢", price: 3520, margin: 4500 },
  { code: "HC2406", name: "热卷", price: 3680, margin: 4800 },
  { code: "I2406", name: "铁矿石", price: 890, margin: 8900 },
  { code: "J2406", name: "焦炭", price: 2150, margin: 12000 },
  { code: "JM2406", name: "焦煤", price: 1580, margin: 9500 },
  { code: "CU2406", name: "铜", price: 76500, margin: 38000 },
  { code: "AL2406", name: "铝", price: 19800, margin: 12000 },
  { code: "ZN2406", name: "锌", price: 22100, margin: 13000 },
  { code: "AU2412", name: "黄金", price: 580, margin: 58000 },
  { code: "AG2412", name: "白银", price: 7200, margin: 14000 },
  { code: "M2409", name: "豆粕", price: 3180, margin: 3200 },
  { code: "Y2409", name: "豆油", price: 7850, margin: 4700 },
  { code: "P2409", name: "棕榈油", price: 7200, margin: 4300 },
  { code: "CF2409", name: "棉花", price: 14500, margin: 7200 },
];

// 开仓原因选项
const openReasons = [
  { value: "news", label: "突发新闻" },
  { value: "personal", label: "个人判断" },
  { value: "technical", label: "技术面突破" },
  { value: "fundamental", label: "基本面变化" },
  { value: "other", label: "其他" },
];

interface ManualOpenPositionModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onConfirm: (data: OpenPositionData) => void;
}

export interface OpenPositionData {
  code: string;
  name: string;
  direction: "long" | "short";
  quantity: number;
  price: number;
  reason: string;
  remark: string;
}

export function ManualOpenPositionModal({
  open,
  onOpenChange,
  onConfirm,
}: ManualOpenPositionModalProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedContract, setSelectedContract] = useState<typeof futuresContracts[0] | null>(null);
  const [direction, setDirection] = useState<"long" | "short">("long");
  const [quantity, setQuantity] = useState(1);
  const [price, setPrice] = useState<number | "">("");
  const [reason, setReason] = useState("");
  const [remark, setRemark] = useState("");
  const [showDropdown, setShowDropdown] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [step, setStep] = useState<1 | 2>(1); // 1: 填写信息, 2: 二次确认

  // 可用保证金（模拟数据）
  const availableMargin = 500000;

  // 过滤期货品种
  const filteredContracts = useMemo(() => {
    if (!searchQuery) return futuresContracts;
    const query = searchQuery.toLowerCase();
    return futuresContracts.filter(
      (c) =>
        c.code.toLowerCase().includes(query) ||
        c.name.toLowerCase().includes(query)
    );
  }, [searchQuery]);

  // 计算可开手数
  const maxQuantity = useMemo(() => {
    if (!selectedContract) return 0;
    return Math.floor(availableMargin / selectedContract.margin);
  }, [selectedContract]);

  // 风控校验
  const riskChecks = useMemo(() => {
    const currentPositionUsage = 78; // 当前仓位使用率
    const positionLimit = 80; // 仓位上限
    const singleContractUsage = selectedContract ? 15 : 0;
    const singleContractLimit = 30;
    const todayLoss = 5000;
    const lossLimit = 50000;
    const isTradingHours = true;

    return [
      {
        label: "仓位使用率",
        current: `${currentPositionUsage}%`,
        limit: `${positionLimit}%`,
        passed: currentPositionUsage < positionLimit,
      },
      {
        label: "单品种仓位",
        current: `${singleContractUsage}%`,
        limit: `${singleContractLimit}%`,
        passed: singleContractUsage < singleContractLimit,
      },
      {
        label: "今日亏损",
        current: todayLoss.toLocaleString(),
        limit: lossLimit.toLocaleString(),
        passed: todayLoss < lossLimit,
      },
      {
        label: "交易时段",
        current: isTradingHours ? "允许" : "禁止",
        limit: "",
        passed: isTradingHours,
      },
    ];
  }, [selectedContract]);

  const allChecksPassed = riskChecks.every((c) => c.passed);

  // 预估保证金和手续费
  const estimatedMargin = selectedContract ? selectedContract.margin * quantity : 0;
  const estimatedFee = selectedContract ? Math.round((price || selectedContract.price) * quantity * 0.0001) : 0;

  const handleSelectContract = (contract: typeof futuresContracts[0]) => {
    setSelectedContract(contract);
    setSearchQuery(contract.code);
    setPrice(contract.price);
    setShowDropdown(false);
  };

  const handleNextStep = () => {
    if (!selectedContract || !reason || quantity < 1) return;
    setStep(2);
  };

  const handleConfirm = async () => {
    if (!selectedContract) return;
    setIsLoading(true);
    
    // 模拟API调用
    await new Promise((resolve) => setTimeout(resolve, 1000));
    
    onConfirm({
      code: selectedContract.code,
      name: selectedContract.name,
      direction,
      quantity,
      price: price || selectedContract.price,
      reason,
      remark,
    });
    
    setIsLoading(false);
    resetForm();
    onOpenChange(false);
  };

  const resetForm = () => {
    setSearchQuery("");
    setSelectedContract(null);
    setDirection("long");
    setQuantity(1);
    setPrice("");
    setReason("");
    setRemark("");
    setStep(1);
  };

  const handleClose = () => {
    resetForm();
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[480px] p-0 gap-0 bg-card border-border">
        <DialogHeader className="px-5 py-4 border-b border-border">
          <DialogTitle className="text-[14px] font-semibold">
            {step === 1 ? "手动开仓" : "确认开仓"}
          </DialogTitle>
        </DialogHeader>

        {step === 1 ? (
          <>
            {/* 表单内容 */}
            <div className="px-5 py-4 space-y-4 max-h-[60vh] overflow-y-auto">
              {/* 品种代码搜索 */}
              <div className="space-y-2">
                <Label className="text-[11px] text-muted-foreground">品种代码</Label>
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                  <Input
                    placeholder="搜索期货代码或名称..."
                    value={searchQuery}
                    onChange={(e) => {
                      setSearchQuery(e.target.value);
                      setShowDropdown(true);
                    }}
                    onFocus={() => setShowDropdown(true)}
                    className="pl-9 h-9 text-[12px]"
                  />
                  {showDropdown && filteredContracts.length > 0 && (
                    <div className="absolute z-50 w-full mt-1 bg-popover border border-border rounded-md shadow-lg max-h-48 overflow-y-auto">
                      {filteredContracts.map((contract) => (
                        <div
                          key={contract.code}
                          className="px-3 py-2 hover:bg-secondary/50 cursor-pointer flex items-center justify-between"
                          onClick={() => handleSelectContract(contract)}
                        >
                          <div>
                            <span className="text-[12px] font-mono font-semibold">{contract.code}</span>
                            <span className="text-[11px] text-muted-foreground ml-2">{contract.name}</span>
                          </div>
                          <span className="text-[11px] font-mono text-primary">{contract.price.toLocaleString()}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              {/* 方向选择 */}
              <div className="space-y-2">
                <Label className="text-[11px] text-muted-foreground">方向</Label>
                <div className="flex gap-2">
                  <Button
                    type="button"
                    variant={direction === "long" ? "default" : "outline"}
                    size="sm"
                    className={cn(
                      "flex-1 h-9 text-[12px]",
                      direction === "long" && "bg-[#EF4444] hover:bg-[#EF4444]/90"
                    )}
                    onClick={() => setDirection("long")}
                  >
                    做多
                  </Button>
                  <Button
                    type="button"
                    variant={direction === "short" ? "default" : "outline"}
                    size="sm"
                    className={cn(
                      "flex-1 h-9 text-[12px]",
                      direction === "short" && "bg-[#22C55E] hover:bg-[#22C55E]/90"
                    )}
                    onClick={() => setDirection("short")}
                  >
                    做空
                  </Button>
                </div>
              </div>

              {/* 手数 */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label className="text-[11px] text-muted-foreground">手数</Label>
                  {selectedContract && (
                    <span className="text-[10px] text-muted-foreground/60">
                      可开 {maxQuantity} 手
                    </span>
                  )}
                </div>
                <Input
                  type="number"
                  min={1}
                  max={maxQuantity || 999}
                  value={quantity}
                  onChange={(e) => setQuantity(Math.max(1, parseInt(e.target.value) || 1))}
                  className="h-9 text-[12px]"
                />
              </div>

              {/* 开仓价格 */}
              <div className="space-y-2">
                <Label className="text-[11px] text-muted-foreground">开仓价格</Label>
                <Input
                  type="number"
                  placeholder={selectedContract ? `当前价: ${selectedContract.price}` : "请先选择品种"}
                  value={price}
                  onChange={(e) => setPrice(e.target.value ? parseFloat(e.target.value) : "")}
                  className="h-9 text-[12px]"
                />
              </div>

              {/* 开仓原因 */}
              <div className="space-y-2">
                <Label className="text-[11px] text-muted-foreground">开仓原因</Label>
                <Select value={reason} onValueChange={setReason}>
                  <SelectTrigger className="h-9 text-[12px]">
                    <SelectValue placeholder="选择开仓原因" />
                  </SelectTrigger>
                  <SelectContent>
                    {openReasons.map((r) => (
                      <SelectItem key={r.value} value={r.value} className="text-[12px]">
                        {r.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* 备注 */}
              <div className="space-y-2">
                <Label className="text-[11px] text-muted-foreground">备注（可选）</Label>
                <Textarea
                  placeholder="输入备注信息..."
                  value={remark}
                  onChange={(e) => setRemark(e.target.value)}
                  className="h-20 text-[12px] resize-none"
                />
              </div>

              {/* 风控校验区域 */}
              <div className="space-y-2 pt-2 border-t border-border">
                <Label className="text-[11px] text-muted-foreground">风控校验</Label>
                <div className="grid grid-cols-2 gap-2">
                  {riskChecks.map((check, idx) => (
                    <div
                      key={idx}
                      className={cn(
                        "flex items-center gap-2 px-3 py-2 rounded-md text-[11px]",
                        check.passed ? "bg-[#22C55E]/10" : "bg-[#EF4444]/10"
                      )}
                    >
                      {check.passed ? (
                        <CheckCircle2 className="w-3.5 h-3.5 text-[#22C55E] flex-shrink-0" />
                      ) : (
                        <XCircle className="w-3.5 h-3.5 text-[#EF4444] flex-shrink-0" />
                      )}
                      <div className="min-w-0">
                        <span className="text-foreground">{check.label}</span>
                        <span className="text-muted-foreground ml-1">
                          {check.current}{check.limit && `/${check.limit}`}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* 底部按钮 */}
            <div className="flex items-center justify-end gap-3 px-5 py-4 border-t border-border bg-muted/20">
              <Button variant="outline" size="sm" onClick={handleClose}>
                取消
              </Button>
              <Button
                size="sm"
                onClick={handleNextStep}
                disabled={!selectedContract || !reason || quantity < 1 || !allChecksPassed}
                className="bg-primary hover:bg-primary/90"
              >
                下一步
              </Button>
            </div>
          </>
        ) : (
          <>
            {/* 二次确认内容 */}
            <div className="px-5 py-4 space-y-4">
              {/* 订单摘要 */}
              <div className="bg-secondary/30 rounded-md p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-[11px] text-muted-foreground">品种</span>
                  <span className="text-[12px] font-mono font-semibold">
                    {selectedContract?.code} {selectedContract?.name}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-[11px] text-muted-foreground">方向</span>
                  <span className={cn(
                    "text-[12px] font-semibold",
                    direction === "long" ? "text-[#EF4444]" : "text-[#22C55E]"
                  )}>
                    {direction === "long" ? "做多" : "做空"}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-[11px] text-muted-foreground">手数</span>
                  <span className="text-[12px] font-mono font-semibold">{quantity} 手</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-[11px] text-muted-foreground">开仓价格</span>
                  <span className="text-[12px] font-mono font-semibold">
                    {(price || selectedContract?.price || 0).toLocaleString()}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-[11px] text-muted-foreground">开仓原因</span>
                  <span className="text-[12px]">
                    {openReasons.find((r) => r.value === reason)?.label}
                  </span>
                </div>
              </div>

              {/* 费用预估 */}
              <div className="bg-secondary/30 rounded-md p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-[11px] text-muted-foreground">预估保证金</span>
                  <span className="text-[12px] font-mono font-semibold text-foreground">
                    {estimatedMargin.toLocaleString()}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-[11px] text-muted-foreground">预估手续费</span>
                  <span className="text-[12px] font-mono font-semibold text-foreground">
                    {estimatedFee.toLocaleString()}
                  </span>
                </div>
              </div>

              {/* 警告 */}
              <div className="bg-warning/10 border border-warning/30 rounded-md p-3">
                <p className="text-[11px] text-warning font-medium">
                  手动开仓不受策略保护，请谨慎操作
                </p>
              </div>
            </div>

            {/* 底部按钮 */}
            <div className="flex items-center justify-end gap-3 px-5 py-4 border-t border-border bg-muted/20">
              <Button variant="outline" size="sm" onClick={() => setStep(1)} disabled={isLoading}>
                返回修改
              </Button>
              <Button
                size="sm"
                onClick={handleConfirm}
                disabled={isLoading}
                className="bg-primary hover:bg-primary/90"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin" />
                    处理中...
                  </>
                ) : (
                  "确认开仓"
                )}
              </Button>
            </div>
          </>
        )}
      </DialogContent>
    </Dialog>
  );
}
