import { ReactNode } from 'react'
import { cn } from '../../utils/cn'

interface MetricCardProps {
  label: string
  value: string | number
  delta?: string
  deltaType?: 'positive' | 'negative' | 'neutral'
  icon?: ReactNode
  className?: string
}

export function MetricCard({ 
  label, 
  value, 
  delta, 
  deltaType = 'neutral',
  icon,
  className 
}: MetricCardProps) {
  const deltaColor = {
    positive: 'text-accent-green',
    negative: 'text-accent-red',
    neutral: 'text-text-muted'
  }

  const deltaIcon = {
    positive: '↑',
    negative: '↓',
    neutral: ''
  }

  return (
    <div className={cn(
      'card p-4 transition-all duration-200 hover:shadow-lg',
      className
    )}>
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <p className="text-xs text-text-muted uppercase tracking-wider font-medium">
            {label}
          </p>
          <p className="text-2xl font-bold text-text-primary mt-1 truncate">
            {value}
          </p>
          {delta && (
            <p className={cn(
              'text-sm font-medium mt-1',
              deltaColor[deltaType]
            )}>
              {deltaIcon[deltaType]} {delta}
            </p>
          )}
        </div>
        {icon && (
          <div className="flex-shrink-0 ml-3 text-text-muted">
            {icon}
          </div>
        )}
      </div>
    </div>
  )
}
