interface StatusDotProps {
  status: 'online' | 'offline'
  size?: 'sm' | 'md'
}

export default function StatusDot({ status, size = 'md' }: StatusDotProps) {
  const sizeClass = size === 'sm' ? 'w-2 h-2' : 'w-3 h-3'
  const colorClass = status === 'online' ? 'bg-success' : 'bg-danger'
  const animate = status === 'online' ? 'animate-pulse-dot' : ''

  return (
    <span
      className={`inline-block rounded-full ${sizeClass} ${colorClass} ${animate}`}
      aria-label={status}
      title={status}
    />
  )
}
