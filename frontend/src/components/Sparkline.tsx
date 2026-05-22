import {
  LineChart,
  Line,
  ResponsiveContainer,
} from 'recharts'

interface SparklineProps {
  data: number[]
  color?: string
}

export default function Sparkline({ data, color = '#3b82f6' }: SparklineProps) {
  const chartData = data.slice(-20).map((value, index) => ({ index, value }))

  if (chartData.length === 0) {
    return <div className="w-full h-[60px] bg-card rounded" />
  }

  return (
    <div className="w-full h-[60px]">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData}>
          <Line
            type="monotone"
            dataKey="value"
            stroke={color}
            strokeWidth={1.5}
            dot={false}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
