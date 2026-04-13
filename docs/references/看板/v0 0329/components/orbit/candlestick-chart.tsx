'use client'

import { useState, useMemo, useCallback } from 'react'
import { cn } from '@/lib/utils'

interface CandlestickChartProps {
  className?: string
  height?: number
}

interface CandleData {
  date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
  isUp: boolean
  macd: number
  dif: number
  dea: number
  k: number
  d: number
  j: number
  rsi: number
}

function generateCandleData(count: number): CandleData[] {
  const data: CandleData[] = []
  let close = 3500

  for (let i = 0; i < count; i++) {
    const date = new Date(2024, 0, i + 1)
    const dateStr = `${(date.getMonth() + 1).toString().padStart(2, '0')}/${date.getDate().toString().padStart(2, '0')}`
    
    const open = close
    const volatility = (Math.random() - 0.5) * 40
    const close_new = close + (Math.random() - 0.5) * 30 + volatility
    const high = Math.max(open, close_new) + Math.random() * 15
    const low = Math.min(open, close_new) - Math.random() * 15
    const volume = Math.floor(Math.random() * 100000) + 50000

    // MACD indicators
    const macd = Math.sin(i * 0.1) * 10
    const dif = Math.sin(i * 0.08) * 8 + 2
    const dea = Math.sin(i * 0.06) * 6 + 1

    // KDJ indicators
    const k = 40 + Math.sin(i * 0.1) * 30
    const d = 45 + Math.sin(i * 0.08) * 25
    const j = 50 + Math.sin(i * 0.12) * 35

    // RSI
    const rsi = 50 + Math.sin(i * 0.15) * 35

    data.push({
      date: dateStr,
      open: Math.round(open * 100) / 100,
      high: Math.round(high * 100) / 100,
      low: Math.round(low * 100) / 100,
      close: Math.round(close_new * 100) / 100,
      volume: volume / 10000,
      isUp: close_new >= open,
      macd,
      dif,
      dea,
      k,
      d,
      j,
      rsi,
    })

    close = close_new
  }

  return data
}

export function CandlestickChart({ className, height = 320 }: CandlestickChartProps) {
  const [period, setPeriod] = useState<'日K' | '周K' | '月K' | '年K'>('日K')
  const [indicator, setIndicator] = useState<'MACD' | 'KDJ' | 'RSI'>('MACD')
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null)
  const candleData = useMemo(() => generateCandleData(60), [])

  const priceMin = Math.min(...candleData.map(d => d.low)) - 10
  const priceMax = Math.max(...candleData.map(d => d.high)) + 10
  const volumeMax = Math.max(...candleData.map(d => d.volume))

  // Calculate chart dimensions
  const chartPadding = { top: 10, right: 50, bottom: 20, left: 10 }
  const mainChartHeight = height * 0.7
  const volumeChartHeight = height * 0.15
  const indicatorChartHeight = 80

  // Price to Y coordinate
  const priceToY = useCallback((price: number) => {
    return chartPadding.top + ((priceMax - price) / (priceMax - priceMin)) * (mainChartHeight - chartPadding.top - 10)
  }, [priceMax, priceMin, mainChartHeight])

  // Volume to Y coordinate
  const volumeToY = useCallback((volume: number) => {
    const volumeAreaTop = mainChartHeight + 5
    const volumeAreaHeight = volumeChartHeight - 10
    return volumeAreaTop + volumeAreaHeight - (volume / volumeMax) * volumeAreaHeight
  }, [volumeMax, mainChartHeight, volumeChartHeight])

  // Indicator to Y coordinate
  const indicatorToY = useCallback((value: number, min: number, max: number) => {
    const indicatorAreaTop = mainChartHeight + volumeChartHeight + 10
    const indicatorAreaHeight = indicatorChartHeight - 30
    return indicatorAreaTop + indicatorAreaHeight - ((value - min) / (max - min)) * indicatorAreaHeight
  }, [mainChartHeight, volumeChartHeight, indicatorChartHeight])

  const totalHeight = mainChartHeight + volumeChartHeight + indicatorChartHeight

  // Get MACD range
  const macdMin = Math.min(...candleData.map(d => Math.min(d.macd, d.dif, d.dea)))
  const macdMax = Math.max(...candleData.map(d => Math.max(d.macd, d.dif, d.dea)))

  return (
    <div className={cn('w-full', className)}>
      <div className="flex items-center gap-2 mb-3 px-1">
        <div className="flex items-center gap-1">
          <span className="text-xs text-muted-foreground">周期:</span>
          {(['日K', '周K', '月K', '年K'] as const).map((p) => (
            <button
              key={p}
              onClick={() => setPeriod(p)}
              className={cn(
                'px-2 py-0.5 text-[10px] font-medium rounded transition-colors',
                period === p ? 'bg-primary/10 text-primary' : 'text-muted-foreground hover:text-foreground',
              )}
            >
              {p}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-1 ml-4">
          <span className="text-xs text-muted-foreground">指标:</span>
          {(['MACD', 'KDJ', 'RSI'] as const).map((ind) => (
            <button
              key={ind}
              onClick={() => setIndicator(ind)}
              className={cn(
                'px-2 py-0.5 text-[10px] font-medium rounded transition-colors',
                indicator === ind ? 'bg-primary/10 text-primary' : 'text-muted-foreground hover:text-foreground',
              )}
            >
              {ind}
            </button>
          ))}
        </div>
      </div>

      {/* Tooltip */}
      {hoveredIndex !== null && (
        <div className="mb-2 px-2 py-1.5 bg-muted/80 rounded text-[10px] flex items-center gap-4">
          <span className="text-muted-foreground">{candleData[hoveredIndex].date}</span>
          <span>开: <span className="font-mono">{candleData[hoveredIndex].open.toFixed(2)}</span></span>
          <span>高: <span className="font-mono text-red-600">{candleData[hoveredIndex].high.toFixed(2)}</span></span>
          <span>低: <span className="font-mono text-emerald-600">{candleData[hoveredIndex].low.toFixed(2)}</span></span>
          <span>收: <span className={cn('font-mono', candleData[hoveredIndex].isUp ? 'text-red-600' : 'text-emerald-600')}>{candleData[hoveredIndex].close.toFixed(2)}</span></span>
          <span>量: <span className="font-mono">{candleData[hoveredIndex].volume.toFixed(1)}万</span></span>
        </div>
      )}

      {/* Main Chart */}
      <div className="w-full rounded-lg border border-border/30 overflow-hidden bg-background/50">
        <svg 
          width="100%" 
          height={totalHeight} 
          viewBox={`0 0 800 ${totalHeight}`}
          preserveAspectRatio="none"
          className="block"
        >
          {/* Grid lines */}
          <defs>
            <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
              <path d="M 40 0 L 0 0 0 40" fill="none" stroke="rgba(156, 163, 175, 0.1)" strokeWidth="0.5"/>
            </pattern>
          </defs>
          <rect width="800" height={mainChartHeight} fill="url(#grid)" />

          {/* Price Y-axis labels */}
          {[0, 0.25, 0.5, 0.75, 1].map((ratio) => {
            const price = priceMin + (priceMax - priceMin) * (1 - ratio)
            const y = chartPadding.top + (mainChartHeight - chartPadding.top - 10) * ratio
            return (
              <g key={ratio}>
                <line x1="0" y1={y} x2="750" y2={y} stroke="rgba(156, 163, 175, 0.15)" strokeWidth="0.5" />
                <text x="760" y={y + 3} fontSize="9" fill="#9ca3af" textAnchor="start">
                  {price.toFixed(0)}
                </text>
              </g>
            )
          })}

          {/* Candlesticks */}
          {candleData.map((candle, index) => {
            const candleWidth = 720 / candleData.length
            const x = 20 + index * candleWidth
            const centerX = x + candleWidth / 2
            const bodyWidth = Math.max(candleWidth * 0.7, 4)

            const openY = priceToY(candle.open)
            const closeY = priceToY(candle.close)
            const highY = priceToY(candle.high)
            const lowY = priceToY(candle.low)

            const bodyTop = Math.min(openY, closeY)
            const bodyHeight = Math.max(Math.abs(closeY - openY), 1)

            const color = candle.isUp ? '#ef4444' : '#22c55e'

            return (
              <g 
                key={index}
                onMouseEnter={() => setHoveredIndex(index)}
                onMouseLeave={() => setHoveredIndex(null)}
                style={{ cursor: 'crosshair' }}
              >
                {/* Wick (upper and lower shadows) */}
                <line
                  x1={centerX}
                  y1={highY}
                  x2={centerX}
                  y2={lowY}
                  stroke={color}
                  strokeWidth={1}
                />
                {/* Body */}
                <rect
                  x={centerX - bodyWidth / 2}
                  y={bodyTop}
                  width={bodyWidth}
                  height={bodyHeight}
                  fill={candle.isUp ? color : color}
                  stroke={color}
                  strokeWidth={0.5}
                />
                {/* Hover highlight */}
                {hoveredIndex === index && (
                  <rect
                    x={x}
                    y={chartPadding.top}
                    width={candleWidth}
                    height={mainChartHeight - chartPadding.top}
                    fill="rgba(59, 130, 246, 0.1)"
                  />
                )}
              </g>
            )
          })}

          {/* Volume bars */}
          {candleData.map((candle, index) => {
            const candleWidth = 720 / candleData.length
            const x = 20 + index * candleWidth
            const barWidth = Math.max(candleWidth * 0.6, 3)
            const barHeight = (candle.volume / volumeMax) * (volumeChartHeight - 15)
            const y = volumeToY(candle.volume)

            return (
              <rect
                key={`vol-${index}`}
                x={x + (candleWidth - barWidth) / 2}
                y={y}
                width={barWidth}
                height={barHeight}
                fill={candle.isUp ? 'rgba(239, 68, 68, 0.4)' : 'rgba(34, 197, 94, 0.4)'}
              />
            )
          })}

          {/* Volume separator line */}
          <line 
            x1="0" 
            y1={mainChartHeight} 
            x2="800" 
            y2={mainChartHeight} 
            stroke="rgba(156, 163, 175, 0.2)" 
            strokeWidth="1" 
          />

          {/* Indicator separator line */}
          <line 
            x1="0" 
            y1={mainChartHeight + volumeChartHeight} 
            x2="800" 
            y2={mainChartHeight + volumeChartHeight} 
            stroke="rgba(156, 163, 175, 0.2)" 
            strokeWidth="1" 
          />

          {/* Indicator - MACD */}
          {indicator === 'MACD' && (
            <g>
              {/* Zero line */}
              <line 
                x1="20" 
                y1={indicatorToY(0, macdMin, macdMax)} 
                x2="740" 
                y2={indicatorToY(0, macdMin, macdMax)} 
                stroke="rgba(156, 163, 175, 0.3)" 
                strokeWidth="0.5" 
              />
              {/* MACD bars */}
              {candleData.map((candle, index) => {
                const candleWidth = 720 / candleData.length
                const x = 20 + index * candleWidth + candleWidth / 2
                const barWidth = Math.max(candleWidth * 0.5, 2)
                const zeroY = indicatorToY(0, macdMin, macdMax)
                const macdY = indicatorToY(candle.macd, macdMin, macdMax)
                const barHeight = Math.abs(macdY - zeroY)

                return (
                  <rect
                    key={`macd-${index}`}
                    x={x - barWidth / 2}
                    y={candle.macd >= 0 ? macdY : zeroY}
                    width={barWidth}
                    height={barHeight}
                    fill={candle.macd >= 0 ? 'rgba(239, 68, 68, 0.6)' : 'rgba(34, 197, 94, 0.6)'}
                  />
                )
              })}
              {/* DIF line */}
              <polyline
                fill="none"
                stroke="#3b82f6"
                strokeWidth="1"
                points={candleData.map((candle, index) => {
                  const candleWidth = 720 / candleData.length
                  const x = 20 + index * candleWidth + candleWidth / 2
                  const y = indicatorToY(candle.dif, macdMin, macdMax)
                  return `${x},${y}`
                }).join(' ')}
              />
              {/* DEA line */}
              <polyline
                fill="none"
                stroke="#f59e0b"
                strokeWidth="1"
                points={candleData.map((candle, index) => {
                  const candleWidth = 720 / candleData.length
                  const x = 20 + index * candleWidth + candleWidth / 2
                  const y = indicatorToY(candle.dea, macdMin, macdMax)
                  return `${x},${y}`
                }).join(' ')}
              />
            </g>
          )}

          {/* Indicator - KDJ */}
          {indicator === 'KDJ' && (
            <g>
              {/* K line */}
              <polyline
                fill="none"
                stroke="#3b82f6"
                strokeWidth="1"
                points={candleData.map((candle, index) => {
                  const candleWidth = 720 / candleData.length
                  const x = 20 + index * candleWidth + candleWidth / 2
                  const y = indicatorToY(candle.k, 0, 100)
                  return `${x},${y}`
                }).join(' ')}
              />
              {/* D line */}
              <polyline
                fill="none"
                stroke="#f59e0b"
                strokeWidth="1"
                points={candleData.map((candle, index) => {
                  const candleWidth = 720 / candleData.length
                  const x = 20 + index * candleWidth + candleWidth / 2
                  const y = indicatorToY(candle.d, 0, 100)
                  return `${x},${y}`
                }).join(' ')}
              />
              {/* J line */}
              <polyline
                fill="none"
                stroke="#a855f7"
                strokeWidth="1"
                points={candleData.map((candle, index) => {
                  const candleWidth = 720 / candleData.length
                  const x = 20 + index * candleWidth + candleWidth / 2
                  const y = indicatorToY(candle.j, 0, 100)
                  return `${x},${y}`
                }).join(' ')}
              />
            </g>
          )}

          {/* Indicator - RSI */}
          {indicator === 'RSI' && (
            <g>
              {/* Overbought line (70) */}
              <line 
                x1="20" 
                y1={indicatorToY(70, 0, 100)} 
                x2="740" 
                y2={indicatorToY(70, 0, 100)} 
                stroke="rgba(239, 68, 68, 0.3)" 
                strokeWidth="0.5" 
                strokeDasharray="3 3"
              />
              {/* Oversold line (30) */}
              <line 
                x1="20" 
                y1={indicatorToY(30, 0, 100)} 
                x2="740" 
                y2={indicatorToY(30, 0, 100)} 
                stroke="rgba(34, 197, 94, 0.3)" 
                strokeWidth="0.5" 
                strokeDasharray="3 3"
              />
              {/* RSI line */}
              <polyline
                fill="none"
                stroke="#a855f7"
                strokeWidth="1"
                points={candleData.map((candle, index) => {
                  const candleWidth = 720 / candleData.length
                  const x = 20 + index * candleWidth + candleWidth / 2
                  const y = indicatorToY(candle.rsi, 0, 100)
                  return `${x},${y}`
                }).join(' ')}
              />
            </g>
          )}

          {/* X-axis date labels */}
          {candleData.filter((_, i) => i % 10 === 0).map((candle, i) => {
            const candleWidth = 720 / candleData.length
            const x = 20 + (i * 10) * candleWidth + candleWidth / 2
            return (
              <text 
                key={candle.date} 
                x={x} 
                y={mainChartHeight - 5} 
                fontSize="9" 
                fill="#9ca3af" 
                textAnchor="middle"
              >
                {candle.date}
              </text>
            )
          })}
        </svg>
      </div>

      {/* Legend */}
      <div className="flex items-center gap-4 mt-2 px-2 text-[10px] text-muted-foreground">
        <span className="flex items-center gap-1">
          <span className="w-2 h-2 bg-red-500 rounded-sm" />
          上涨
        </span>
        <span className="flex items-center gap-1">
          <span className="w-2 h-2 bg-emerald-500 rounded-sm" />
          下跌
        </span>
        {indicator === 'MACD' && (
          <>
            <span className="flex items-center gap-1">
              <span className="w-3 h-0.5 bg-blue-500 rounded" />
              DIF
            </span>
            <span className="flex items-center gap-1">
              <span className="w-3 h-0.5 bg-amber-500 rounded" />
              DEA
            </span>
          </>
        )}
        {indicator === 'KDJ' && (
          <>
            <span className="flex items-center gap-1">
              <span className="w-3 h-0.5 bg-blue-500 rounded" />
              K
            </span>
            <span className="flex items-center gap-1">
              <span className="w-3 h-0.5 bg-amber-500 rounded" />
              D
            </span>
            <span className="flex items-center gap-1">
              <span className="w-3 h-0.5 bg-purple-500 rounded" />
              J
            </span>
          </>
        )}
        {indicator === 'RSI' && (
          <span className="flex items-center gap-1">
            <span className="w-3 h-0.5 bg-purple-500 rounded" />
            RSI(14)
          </span>
        )}
      </div>
    </div>
  )
}
