"use client";

import { cn } from "@/lib/utils";
import type { Sentiment } from "@/lib/mock-data";
import { HealthGauge } from "./health-gauge";

interface SentimentOrbProps {
  sentiment: Sentiment;
  healthScore: number;
}

const sentimentConfig = {
  positive: {
    label: "健康",
    color: "text-success",
    bgColor: "bg-success/6",
    badgeClass: "bg-success/8 text-success",
  },
  neutral: {
    label: "稳定",
    color: "text-muted-foreground",
    bgColor: "bg-secondary/50",
    badgeClass: "bg-secondary text-muted-foreground",
  },
  negative: {
    label: "风险",
    color: "text-warning",
    bgColor: "bg-warning/6",
    badgeClass: "bg-warning/8 text-warning",
  },
  critical: {
    label: "危急",
    color: "text-critical",
    bgColor: "bg-critical/6",
    badgeClass: "bg-critical/8 text-critical",
  },
};

export function SentimentOrb({ sentiment, healthScore }: SentimentOrbProps) {
  const config = sentimentConfig[sentiment];

  return (
    <div className="bg-card rounded-md p-6 h-full min-h-[220px] flex flex-col items-center justify-center">
      {/* Header */}
      <p className="text-[10px] font-medium text-muted-foreground/60 uppercase tracking-wider mb-4">
        账户健康度
      </p>

      {/* Health Gauge */}
      <div className={cn("p-4 rounded-lg", config.bgColor)}>
        <HealthGauge 
          score={healthScore} 
          size="lg" 
          showLabel={false}
        />
      </div>

      {/* Status Badge */}
      <div className="mt-4 text-center">
        <span
          className={cn(
            "inline-flex items-center px-3 py-1 rounded-md text-[12px] font-medium",
            config.badgeClass
          )}
        >
          {config.label}
        </span>
        <p className="text-[10px] text-muted-foreground/40 mt-2">
          悬停仪表盘查看详情
        </p>
      </div>
    </div>
  );
}
