import { cn } from '../../utils/cn'

interface BenchmarkGaugeProps {
  value: number
  max?: number
  label: string
  unit?: string
  color?: 'blue' | 'cyan' | 'green' | 'yellow' | 'red'
  size?: 'sm' | 'md' | 'lg'
  className?: string
}

const colorMap = {
  blue: { stroke: '#6366F1', bg: 'stroke-accent-blue/20' },
  cyan: { stroke: '#06B6D4', bg: 'stroke-accent-cyan/20' },
  green: { stroke: '#10B981', bg: 'stroke-accent-green/20' },
  yellow: { stroke: '#F59E0B', bg: 'stroke-accent-yellow/20' },
  red: { stroke: '#EF4444', bg: 'stroke-accent-red/20' }
}

const sizeMap = {
  sm: { width: 80, strokeWidth: 6, fontSize: 'text-lg' },
  md: { width: 120, strokeWidth: 8, fontSize: 'text-2xl' },
  lg: { width: 160, strokeWidth: 10, fontSize: 'text-3xl' }
}

export function BenchmarkGauge({
  value,
  max = 100,
  label,
  unit = '',
  color = 'blue',
  size = 'md',
  className
}: BenchmarkGaugeProps) {
  const percentage = Math.min((value / max) * 100, 100)
  const colors = colorMap[color]
  const dimensions = sizeMap[size]

  // Calculate arc
  const radius = (dimensions.width - dimensions.strokeWidth) / 2
  const circumference = Math.PI * radius
  const strokeLength = (percentage / 100) * circumference

  return (
    <div className={cn('flex flex-col items-center', className)}>
      <svg
        width={dimensions.width}
        height={dimensions.width / 2 + 20}
        viewBox={`0 0 ${dimensions.width} ${dimensions.width / 2 + 20}`}
      >
        {/* Background arc */}
        <path
          d={`M ${dimensions.strokeWidth / 2} ${dimensions.width / 2} A ${radius} ${radius} 0 0 1 ${dimensions.width - dimensions.strokeWidth / 2} ${dimensions.width / 2}`}
          fill="none"
          className={colors.bg}
          strokeWidth={dimensions.strokeWidth}
          strokeLinecap="round"
        />

        {/* Value arc */}
        <path
          d={`M ${dimensions.strokeWidth / 2} ${dimensions.width / 2} A ${radius} ${radius} 0 0 1 ${dimensions.width - dimensions.strokeWidth / 2} ${dimensions.width / 2}`}
          fill="none"
          stroke={colors.stroke}
          strokeWidth={dimensions.strokeWidth}
          strokeLinecap="round"
          strokeDasharray={`${strokeLength} ${circumference}`}
          className="transition-all duration-500"
        />

        {/* Value text */}
        <text
          x={dimensions.width / 2}
          y={dimensions.width / 2 - 10}
          textAnchor="middle"
          className="fill-text-primary font-bold"
          style={{ fontSize: dimensions.width * 0.2 }}
        >
          {value}{unit}
        </text>
      </svg>

      <p className="text-sm text-text-muted mt-2">{label}</p>
    </div>
  )
}
