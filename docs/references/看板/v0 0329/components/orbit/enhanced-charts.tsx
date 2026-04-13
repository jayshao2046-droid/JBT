"use client";

import React, { useState, useCallback, useMemo } from "react";
import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  ZAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  Legend,
} from "recharts";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import { ChevronRight, ZoomIn, ZoomOut, RotateCcw } from "lucide-react";

// ==================== Radar Chart Component ====================

interface RadarDataPoint {
  subject: string;
  value: number;
  fullMark?: number;
}

interface EnhancedRadarChartProps {
  data: RadarDataPoint[];
  title?: string;
  color?: string;
  fillOpacity?: number;
  className?: string;
  onPointClick?: (point: RadarDataPoint) => void;
}

export function EnhancedRadarChart({
  data,
  title,
  color = "hsl(var(--primary))",
  fillOpacity = 0.3,
  className,
  onPointClick,
}: EnhancedRadarChartProps) {
  const [activeIndex, setActiveIndex] = useState<number | null>(null);

  return (
    <div className={cn("w-full", className)}>
      {title && (
        <h3 className="text-sm font-semibold text-foreground mb-4">{title}</h3>
      )}
      <ResponsiveContainer width="100%" height={300}>
        <RadarChart cx="50%" cy="50%" outerRadius="80%" data={data}>
          <PolarGrid stroke="hsl(var(--border))" />
          <PolarAngleAxis
            dataKey="subject"
            tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 11 }}
          />
          <PolarRadiusAxis
            angle={30}
            domain={[0, 100]}
            tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 10 }}
          />
          <Radar
            name="数值"
            dataKey="value"
            stroke={color}
            fill={color}
            fillOpacity={fillOpacity}
            animationDuration={800}
            animationEasing="ease-out"
            onMouseEnter={(_, index) => setActiveIndex(index)}
            onMouseLeave={() => setActiveIndex(null)}
            onClick={(_, index) => onPointClick?.(data[index])}
          />
          <Tooltip
            content={({ active, payload }) => {
              if (active && payload && payload.length) {
                const point = payload[0].payload as RadarDataPoint;
                return (
                  <div className="bg-popover border border-border rounded-lg px-3 py-2 shadow-lg">
                    <p className="text-sm font-medium text-foreground">{point.subject}</p>
                    <p className="text-xs text-muted-foreground">
                      数值: <span className="text-foreground font-medium">{point.value}</span>
                    </p>
                  </div>
                );
              }
              return null;
            }}
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}

// ==================== Scatter Chart Component ====================

interface ScatterDataPoint {
  x: number;
  y: number;
  z?: number;
  name?: string;
  category?: string;
}

interface EnhancedScatterChartProps {
  data: ScatterDataPoint[];
  title?: string;
  xLabel?: string;
  yLabel?: string;
  colorByCategory?: boolean;
  className?: string;
  onPointClick?: (point: ScatterDataPoint) => void;
}

const CATEGORY_COLORS = [
  "hsl(var(--primary))",
  "hsl(var(--chart-2))",
  "hsl(var(--chart-3))",
  "hsl(var(--chart-4))",
  "hsl(var(--chart-5))",
];

export function EnhancedScatterChart({
  data,
  title,
  xLabel = "X轴",
  yLabel = "Y轴",
  colorByCategory = false,
  className,
  onPointClick,
}: EnhancedScatterChartProps) {
  const [zoom, setZoom] = useState(1);
  const [hoveredPoint, setHoveredPoint] = useState<ScatterDataPoint | null>(null);

  const categories = useMemo(() => {
    if (!colorByCategory) return [];
    return [...new Set(data.map((d) => d.category).filter(Boolean))];
  }, [data, colorByCategory]);

  const groupedData = useMemo(() => {
    if (!colorByCategory || categories.length === 0) {
      return [{ name: "数据点", data, color: CATEGORY_COLORS[0] }];
    }
    return categories.map((cat, i) => ({
      name: cat!,
      data: data.filter((d) => d.category === cat),
      color: CATEGORY_COLORS[i % CATEGORY_COLORS.length],
    }));
  }, [data, colorByCategory, categories]);

  const handleZoomIn = () => setZoom((z) => Math.min(z + 0.2, 2));
  const handleZoomOut = () => setZoom((z) => Math.max(z - 0.2, 0.5));
  const handleReset = () => setZoom(1);

  return (
    <div className={cn("w-full", className)}>
      <div className="flex items-center justify-between mb-4">
        {title && <h3 className="text-sm font-semibold text-foreground">{title}</h3>}
        <div className="flex items-center gap-1">
          <button
            onClick={handleZoomOut}
            className="p-1.5 rounded hover:bg-muted transition-colors"
            title="缩小"
          >
            <ZoomOut className="w-4 h-4" />
          </button>
          <button
            onClick={handleZoomIn}
            className="p-1.5 rounded hover:bg-muted transition-colors"
            title="放大"
          >
            <ZoomIn className="w-4 h-4" />
          </button>
          <button
            onClick={handleReset}
            className="p-1.5 rounded hover:bg-muted transition-colors"
            title="重置"
          >
            <RotateCcw className="w-4 h-4" />
          </button>
        </div>
      </div>
      <ResponsiveContainer width="100%" height={300}>
        <ScatterChart
          margin={{ top: 20, right: 20, bottom: 20, left: 20 }}
        >
          <CartesianGrid stroke="hsl(var(--border))" strokeDasharray="3 3" />
          <XAxis
            type="number"
            dataKey="x"
            name={xLabel}
            tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 11 }}
            domain={[`dataMin * ${1/zoom}`, `dataMax * ${zoom}`]}
          />
          <YAxis
            type="number"
            dataKey="y"
            name={yLabel}
            tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 11 }}
            domain={[`dataMin * ${1/zoom}`, `dataMax * ${zoom}`]}
          />
          <ZAxis type="number" dataKey="z" range={[60, 400]} />
          <Tooltip
            content={({ active, payload }) => {
              if (active && payload && payload.length) {
                const point = payload[0].payload as ScatterDataPoint;
                return (
                  <div className="bg-popover border border-border rounded-lg px-3 py-2 shadow-lg">
                    {point.name && (
                      <p className="text-sm font-medium text-foreground mb-1">{point.name}</p>
                    )}
                    <p className="text-xs text-muted-foreground">
                      {xLabel}: <span className="text-foreground">{point.x.toFixed(2)}</span>
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {yLabel}: <span className="text-foreground">{point.y.toFixed(2)}</span>
                    </p>
                    {point.z && (
                      <p className="text-xs text-muted-foreground">
                        大小: <span className="text-foreground">{point.z.toFixed(2)}</span>
                      </p>
                    )}
                  </div>
                );
              }
              return null;
            }}
          />
          {colorByCategory && categories.length > 0 && (
            <Legend
              wrapperStyle={{ fontSize: 11 }}
            />
          )}
          {groupedData.map((group) => (
            <Scatter
              key={group.name}
              name={group.name}
              data={group.data}
              fill={group.color}
              animationDuration={800}
              onClick={(point) => onPointClick?.(point as unknown as ScatterDataPoint)}
            />
          ))}
        </ScatterChart>
      </ResponsiveContainer>
    </div>
  );
}

// ==================== Drill Down Chart Wrapper ====================

interface DrillDownLevel {
  id: string;
  title: string;
  data: unknown[];
}

interface DrillDownChartProps {
  levels: DrillDownLevel[];
  currentLevel: number;
  onDrillDown: (itemId: string, nextLevel: number) => void;
  onDrillUp: () => void;
  renderChart: (data: unknown[], level: number, onItemClick: (id: string) => void) => React.ReactNode;
  className?: string;
}

export function DrillDownChart({
  levels,
  currentLevel,
  onDrillDown,
  onDrillUp,
  renderChart,
  className,
}: DrillDownChartProps) {
  const currentData = levels[currentLevel];

  const handleItemClick = useCallback(
    (itemId: string) => {
      if (currentLevel < levels.length - 1) {
        onDrillDown(itemId, currentLevel + 1);
      }
    },
    [currentLevel, levels.length, onDrillDown]
  );

  return (
    <div className={cn("w-full", className)}>
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 mb-4 text-sm">
        {levels.slice(0, currentLevel + 1).map((level, index) => (
          <React.Fragment key={level.id}>
            {index > 0 && <ChevronRight className="w-4 h-4 text-muted-foreground" />}
            <button
              onClick={() => index < currentLevel && onDrillUp()}
              className={cn(
                "transition-colors",
                index === currentLevel
                  ? "text-foreground font-medium"
                  : "text-muted-foreground hover:text-foreground"
              )}
              disabled={index === currentLevel}
            >
              {level.title}
            </button>
          </React.Fragment>
        ))}
      </div>

      {/* Chart with animation */}
      <AnimatePresence mode="wait">
        <motion.div
          key={currentLevel}
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -20 }}
          transition={{ duration: 0.2 }}
        >
          {renderChart(currentData.data, currentLevel, handleItemClick)}
        </motion.div>
      </AnimatePresence>

      {/* Drill up hint */}
      {currentLevel > 0 && (
        <button
          onClick={onDrillUp}
          className="mt-4 text-xs text-muted-foreground hover:text-foreground flex items-center gap-1"
        >
          <ChevronRight className="w-3 h-3 rotate-180" />
          返回上一级
        </button>
      )}
    </div>
  );
}

// ==================== Animated Number ====================

interface AnimatedNumberProps {
  value: number;
  duration?: number;
  formatFn?: (value: number) => string;
  className?: string;
}

export function AnimatedNumber({
  value,
  duration = 1000,
  formatFn = (v) => v.toFixed(0),
  className,
}: AnimatedNumberProps) {
  const [displayValue, setDisplayValue] = React.useState(0);

  React.useEffect(() => {
    const startTime = Date.now();
    const startValue = displayValue;
    const diff = value - startValue;

    const animate = () => {
      const elapsed = Date.now() - startTime;
      const progress = Math.min(elapsed / duration, 1);
      
      // Easing function (ease-out-cubic)
      const eased = 1 - Math.pow(1 - progress, 3);
      
      setDisplayValue(startValue + diff * eased);

      if (progress < 1) {
        requestAnimationFrame(animate);
      }
    };

    requestAnimationFrame(animate);
  }, [value, duration]);

  return <span className={className}>{formatFn(displayValue)}</span>;
}

// ==================== Chart Skeleton ====================

export function ChartSkeleton({ className }: { className?: string }) {
  return (
    <div className={cn("animate-pulse", className)}>
      <div className="h-4 bg-muted rounded w-1/3 mb-4" />
      <div className="h-[250px] bg-muted/50 rounded-lg flex items-end justify-around p-4 gap-2">
        {Array.from({ length: 8 }).map((_, i) => (
          <div
            key={i}
            className="bg-muted rounded"
            style={{
              width: "8%",
              height: `${Math.random() * 60 + 20}%`,
            }}
          />
        ))}
      </div>
    </div>
  );
}
