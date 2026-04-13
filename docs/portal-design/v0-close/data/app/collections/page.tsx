'use client'

import { useState, useEffect } from 'react'
import { DataQualityKPI } from '@/components/DataQualityKPI'
import { DataSourceHealthKPI } from '@/components/DataSourceHealthKPI'
import { DataSourceAnalysis } from '@/components/DataSourceAnalysis'
import { CollectionStatsChart } from '@/components/CollectionStatsChart'
import { dataAPI } from '@/lib/data-api'

export default function CollectionsPage() {
  const [qualityMetrics, setQualityMetrics] = useState({
    completeness: 95.5,
    timeliness: 98.2,
    accuracy: 99.1,
    consistency: 97.8,
    success_rate: 96.5,
    avg_latency: 3.2,
    error_rate: 3.5,
  })

  const [healthMetrics, setHealthMetrics] = useState({
    availability: 99.2,
    response_time: 150,
    error_rate: 0.8,
    freshness: 98.5,
    coverage: 97.3,
  })

  const [sources, setSources] = useState([
    {
      id: 'futures',
      name: '期货分钟数据',
      category: '行情类',
      status: 'available',
      availability: 99.5,
      response_time: 120,
      coverage: 98.0,
    },
    {
      id: 'stock',
      name: '股票分钟数据',
      category: '行情类',
      status: 'available',
      availability: 98.8,
      response_time: 180,
      coverage: 97.5,
    },
  ])

  const [chartData, setChartData] = useState([
    { time: '09:00', count: 1500, duration: 120 },
    { time: '10:00', count: 1800, duration: 135 },
    { time: '11:00', count: 1650, duration: 128 },
    { time: '14:00', count: 1900, duration: 142 },
    { time: '15:00', count: 1750, duration: 130 },
  ])

  return (
    <div className="container mx-auto p-6 space-y-6">
      <h1 className="text-3xl font-bold">数据采集看板</h1>

      <DataQualityKPI metrics={qualityMetrics} />
      <DataSourceHealthKPI metrics={healthMetrics} />
      <CollectionStatsChart data={chartData} />
      <DataSourceAnalysis sources={sources} />
    </div>
  )
}
