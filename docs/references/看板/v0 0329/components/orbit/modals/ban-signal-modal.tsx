"use client";

import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { AlertTriangle } from "lucide-react";
import { cn } from "@/lib/utils";

export interface BanSignalData {
  code: string;
  signal: string;
  confidence: number;
  strategyName: string;
  type: "buy" | "sell" | "hold";
}

interface BanSignalModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  signal: BanSignalData | null;
  onConfirm: (banType: "temporary" | "permanent", hours?: number) => void;
}

export function BanSignalModal({
  open,
  onOpenChange,
  signal,
  onConfirm,
}: BanSignalModalProps) {
  const [banType, setBanType] = useState<"temporary" | "permanent">("temporary");
  const [hours, setHours] = useState<string>("4");

  if (!signal) return null;

  const handleConfirm = () => {
    onConfirm(banType, banType === "temporary" ? parseInt(hours) : undefined);
    onOpenChange(false);
  };

  const getDirectionText = (type: string) => {
    if (type === "buy") return "看多";
    if (type === "sell") return "看空";
    return "观望";
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[420px]">
        <DialogHeader>
          <DialogTitle className="text-base font-semibold">禁止策略信号</DialogTitle>
          <DialogDescription className="text-xs text-muted-foreground">
            禁止后该策略将不再发出自动交易信号
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* 信号信息 */}
          <div className="bg-secondary/30 rounded-md p-3 space-y-2">
            <div className="grid grid-cols-2 gap-2 text-[11px]">
              <div>
                <span className="text-muted-foreground">品种：</span>
                <span className="font-mono font-semibold text-foreground ml-1">{signal.code}</span>
              </div>
              <div>
                <span className="text-muted-foreground">方向：</span>
                <span
                  className={cn(
                    "font-semibold ml-1",
                    signal.type === "buy" && "text-[#EF4444]",
                    signal.type === "sell" && "text-[#22C55E]",
                    signal.type === "hold" && "text-muted-foreground"
                  )}
                >
                  {getDirectionText(signal.type)}
                </span>
              </div>
              <div>
                <span className="text-muted-foreground">置信度：</span>
                <span className="font-mono font-semibold text-foreground ml-1">{signal.confidence}%</span>
              </div>
              <div>
                <span className="text-muted-foreground">策略：</span>
                <span className="font-semibold text-foreground ml-1">{signal.strategyName}</span>
              </div>
            </div>
          </div>

          {/* 禁止方式选择 */}
          <div className="space-y-3">
            <Label className="text-[11px] text-muted-foreground">禁止方式</Label>
            <RadioGroup
              value={banType}
              onValueChange={(v) => setBanType(v as "temporary" | "permanent")}
              className="space-y-2"
            >
              <div className="flex items-center space-x-3">
                <RadioGroupItem value="temporary" id="temporary" />
                <Label htmlFor="temporary" className="text-[11px] font-normal cursor-pointer flex items-center gap-2">
                  临时禁止
                  <Select value={hours} onValueChange={setHours} disabled={banType !== "temporary"}>
                    <SelectTrigger className="w-[100px] h-7 text-[11px]">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="1" className="text-[11px]">1 小时</SelectItem>
                      <SelectItem value="2" className="text-[11px]">2 小时</SelectItem>
                      <SelectItem value="4" className="text-[11px]">4 小时</SelectItem>
                      <SelectItem value="8" className="text-[11px]">8 小时</SelectItem>
                      <SelectItem value="24" className="text-[11px]">24 小时</SelectItem>
                    </SelectContent>
                  </Select>
                </Label>
              </div>
              <div className="flex items-center space-x-3">
                <RadioGroupItem value="permanent" id="permanent" />
                <Label htmlFor="permanent" className="text-[11px] font-normal cursor-pointer">
                  永久禁止（需手动恢复）
                </Label>
              </div>
            </RadioGroup>
          </div>

          {/* 警告文字 */}
          <div className="flex items-start gap-2 p-2.5 bg-destructive/10 rounded-md">
            <AlertTriangle className="w-4 h-4 text-destructive flex-shrink-0 mt-0.5" />
            <p className="text-[10px] text-destructive">
              禁止后该策略将不再发出自动交易信号
            </p>
          </div>
        </div>

        <DialogFooter className="gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => onOpenChange(false)}
            className="h-8 text-[11px]"
          >
            取消
          </Button>
          <Button
            variant="destructive"
            size="sm"
            onClick={handleConfirm}
            className="h-8 text-[11px]"
          >
            确认禁止
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
