import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'
import type { MetricResponse } from '@/types'

interface MetricChartProps {
  data: MetricResponse[]
  dataKey: keyof Pick<MetricResponse, 'cpu_percent' | 'ram_percent' | 'disk_percent' | 'net_rx_bytes'>
  color?: string
  title: string
  unit?: string
}

export default function MetricChart({
  data,
  dataKey,
  color = '#3b82f6',
  title,
  unit = '%',
}: MetricChartProps) {
  const chartData = data.map((m) => ({
    time: new Date(m.recorded_at).toLocaleTimeString([], {
      hour: '2-digit',
      minute: '2-digit',
    }),
    value: m[dataKey],
  }))

  return (
    <div className="bg-card border border-border rounded-lg p-4">
      <h3 className="text-sm font-medium text-gray-300 mb-2">{title}</h3>
      {chartData.length === 0 ? (
        <div className="h-[180px] flex items-center justify-center text-gray-500 text-sm">
          No data available
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={180}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#2a2d37" />
            <XAxis
              dataKey="time"
              tick={{ fontSize: 10, fill: '#6b7280' }}
              tickLine={false}
              axisLine={{ stroke: '#2a2d37' }}
            />
            <YAxis
              tick={{ fontSize: 10, fill: '#6b7280' }}
              tickLine={false}
              axisLine={{ stroke: '#2a2d37' }}
              unit={unit}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#1a1c23',
                border: '1px solid #2a2d37',
                borderRadius: '6px',
                fontSize: '12px',
              }}
              labelStyle={{ color: '#9ca3af' }}
              itemStyle={{ color: '#e5e7eb' }}
              formatter={(value: number) => [`${value.toFixed(1)}${unit}`, title]}
            />
            <Line
              type="monotone"
              dataKey="value"
              stroke={color}
              strokeWidth={2}
              dot={false}
              isAnimationActive={false}
            />
          </LineChart>
        </ResponsiveContainer>
      )}
    </div>
  )
}
