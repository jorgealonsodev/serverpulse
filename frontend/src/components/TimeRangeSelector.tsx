import type { TimeRange } from '@/types'

interface TimeRangeSelectorProps {
  value: TimeRange
  onChange: (range: TimeRange) => void
}

const RANGES: TimeRange[] = ['1h', '6h', '24h']

export default function TimeRangeSelector({ value, onChange }: TimeRangeSelectorProps) {
  return (
    <div className="inline-flex bg-card border border-border rounded-lg p-1 gap-1">
      {RANGES.map((range) => (
        <button
          key={range}
          onClick={() => onChange(range)}
          className={`px-3 py-1 text-sm rounded-md transition-colors ${
            value === range
              ? 'bg-accent text-white'
              : 'text-gray-400 hover:text-white hover:bg-border'
          }`}
        >
          {range}
        </button>
      ))}
    </div>
  )
}
