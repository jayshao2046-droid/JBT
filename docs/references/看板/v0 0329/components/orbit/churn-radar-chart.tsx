"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { cn } from "@/lib/utils";
import { TrendingUp } from "lucide-react";

// 不同时间周期的数据
const dailyData = [
  { time: '09:00', value: 0 },
  { time: '09:30', value: 0.3 },
  { time: '10:00', value: 1.2 },
  { time: '10:30', value: 0.8 },
  { time: '11:00', value: 2.1 },
  { time: '11:30', value: 1.5 },
  { time: '12:00', value: 1.6 },
  { time: '13:00', value: 2.3 },
  { time: '13:30', value: 1.8 },
  { time: '14:00', value: 2.8 },
  { time: '14:30', value: 2.2 },
  { time: '15:00', value: 3.1 },
  { time: '15:30', value: 2.9 },
  { time: '16:00', value: 3.3 },
  { time: '17:00', value: 3.0 },
  { time: '18:00', value: 3.5 },
  { time: '19:00', value: 3.2 },
  { time: '20:00', value: 3.8 },
  { time: '21:00', value: 3.6 },
  { time: '22:00', value: 4.0 },
  { time: '23:00', value: 3.9 },
];

const weeklyData = [
  { time: '周一', value: 1.2 },
  { time: '周二', value: 2.5 },
  { time: '周三', value: 1.8 },
  { time: '周四', value: 3.2 },
  { time: '周五', value: 2.8 },
  { time: '周六', value: 3.1 },
  { time: '周日', value: 3.5 },
];

const monthlyData = Array.from({ length: 31 }, (_, i) => ({
  time: `${i + 1}日`,
  value: parseFloat((Math.sin(i * 0.4) * 1.5 + i * 0.12 + 0.5).toFixed(2)),
}));

const yearlyData = [
  { time: '1月', value: 2.1 },
  { time: '2月', value: 3.5 },
  { time: '3月', value: 2.8 },
  { time: '4月', value: 4.2 },
  { time: '5月', value: 3.8 },
  { time: '6月', value: 5.1 },
  { time: '7月', value: 4.5 },
  { time: '8月', value: 6.2 },
  { time: '9月', value: 5.8 },
  { time: '10月', value: 7.1 },
  { time: '11月', value: 6.5 },
  { time: '12月', value: 8.2 },
];

// 全部：过去90天
const allData = Array.from({ length: 91 }, (_, i) => {
  const date = new Date()
  date.setDate(date.getDate() - (90 - i))
  return {
    time: `${date.getMonth() + 1}/${date.getDate()}`,
    value: parseFloat((Math.sin(i * 0.15) * 2 + i * 0.06 + 0.5).toFixed(2)),
  }
})

type TimeRange = 'day' | 'week' | 'month' | 'year' | 'all';

const timeRangeConfig: { id: TimeRange; label: string }[] = [
  { id: 'day', label: '日' },
  { id: 'week', label: '周' },
  { id: 'month', label: '月' },
  { id: 'year', label: '年' },
  { id: 'all', label: '全部' },
];

interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{
    name: string;
    value: number;
    color: string;
    dataKey: string;
  }>;
  label?: string;
}

function CustomTooltip({ active, payload, label }: CustomTooltipProps) {
  if (!active || !payload) return null;

  return (
    <motion.div 
      initial={{ opacity: 0, y: 4 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-popover p-3 rounded-md shadow-lg"
    >
      <p className="text-[11px] font-medium text-foreground mb-1.5">{label}</p>
      {payload.map((entry, index) => (
        <div key={index} className="flex items-center gap-2 text-[10px]">
          <div
            className="w-1.5 h-1.5 rounded-full"
            style={{ backgroundColor: entry.color }}
          />
          <span className="text-muted-foreground/70">收益:</span>
          <span className={cn(
            "font-mono font-medium",
            entry.value >= 0 ? "text-[#EF4444]" : "text-[#22C55E]"
          )}>
            {entry.value >= 0 ? '+' : ''}{entry.value}%
          </span>
        </div>
      ))}
    </motion.div>
  );
}

// 四个指标卡片
interface IndicatorProps {
  label: string;
  value: string;
  change: string;
  isPositive: boolean;
}

function Indicator({ label, value, change, isPositive }: IndicatorProps) {
  return (
    <div className="text-center">
      <p className="text-[10px] text-muted-foreground/60 mb-1">{label}</p>
      <p className="text-[14px] font-mono font-semibold text-foreground">{value}</p>
      <p className={cn(
        "text-[10px] font-mono",
        isPositive ? "text-[#EF4444]" : "text-[#22C55E]"
      )}>
        {isPositive ? '+' : ''}{change}
      </p>
    </div>
  );
}

export function ChurnRadarChart() {
  const [timeRange, setTimeRange] = useState<TimeRange>('day');

  const getChartData = () => {
    switch (timeRange) {
      case 'day': return dailyData;
      case 'week': return weeklyData;
      case 'month': return monthlyData;
      case 'year': return yearlyData;
      case 'all': return allData;
      default: return dailyData;
    }
  };

  const chartData = getChartData();

  return (
    <div>
      <div className="flex items-center justify-between mb-5">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-md bg-primary/10 flex items-center justify-center">
            <TrendingUp className="w-3.5 h-3.5 text-primary" strokeWidth={1.5} />
          </div>
          <div>
            <h3 className="text-[13px] font-medium text-foreground">
              收益表
            </h3>
            <p className="text-[11px] text-muted-foreground/60 mt-0.5">
              收益走势分析
            </p>
          </div>
        </div>
        {/* 时间切换按钮 */}
        <div className="flex items-center gap-1 bg-secondary/40 rounded-md p-0.5">
          {timeRangeConfig.map((item) => (
            <button
              key={item.id}
              onClick={() => setTimeRange(item.id)}
              className={cn(
                "px-3 py-1 text-[11px] font-medium rounded transition-all duration-100",
                timeRange === item.id
                  ? "bg-card text-foreground shadow-sm"
                  : "text-muted-foreground hover:text-foreground"
              )}
            >
              {item.label}
            </button>
          ))}
        </div>
      </div>

      {/* 四个指标 */}
      <div className="grid grid-cols-4 gap-4 mb-4 px-2">
        <Indicator 
          label="总收益" 
          value="41,200" 
          change="8.2%" 
          isPositive={true} 
        />
        <Indicator 
          label="最大回撤" 
          value="-2.3%" 
          change="-0.5%" 
          isPositive={false} 
        />
        <Indicator 
          label="胜率" 
          value="68.5%" 
          change="3.2%" 
          isPositive={true} 
        />
        <Indicator 
          label="盈亏比" 
          value="2.15" 
          change="0.12" 
          isPositive={true} 
        />
      </div>

      <div className="h-[240px]">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart
            data={chartData}
            margin={{ top: 10, right: 10, left: -10, bottom: 0 }}
          >
            <defs>
              <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#EF4444" stopOpacity={0.15} />
                <stop offset="95%" stopColor="#EF4444" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="rgba(0,0,0,0.04)"
              vertical={false}
            />
            <XAxis
              dataKey="time"
              stroke="rgba(0,0,0,0.3)"
              fontSize={10}
              tickLine={false}
              axisLine={false}
              dy={8}
            />
            <YAxis
              stroke="rgba(0,0,0,0.3)"
              fontSize={10}
              tickLine={false}
              axisLine={false}
              tickFormatter={(value) => `${value}%`}
              dx={-5}
            />
            <Tooltip content={<CustomTooltip />} />
            <Area
              type="monotone"
              dataKey="value"
              stroke="#EF4444"
              strokeWidth={1.5}
              fillOpacity={1}
              fill="url(#colorValue)"
              name="收益"
              dot={false}
              activeDot={{
                r: 4,
                fill: "#EF4444",
                stroke: "#FFFFFF",
                strokeWidth: 2,
              }}
              animationDuration={600}
              animationEasing="ease-out"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
