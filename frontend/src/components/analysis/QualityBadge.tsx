import { cn } from '../../utils/cn'
import { Check, AlertTriangle, X, Info, Star } from 'lucide-react'

export type QualityGrade = 'A' | 'B' | 'C' | 'D' | 'F'

interface QualityBadgeProps {
  grade: QualityGrade
  showDetails?: boolean
  confidence?: number
  className?: string
}

const gradeConfig = {
  A: {
    color: 'text-accent-green',
    bg: 'bg-accent-green/10',
    border: 'border-accent-green/30',
    icon: Star,
    label: 'Excellent',
    description: 'High confidence, comprehensive analysis'
  },
  B: {
    color: 'text-accent-cyan',
    bg: 'bg-accent-cyan/10',
    border: 'border-accent-cyan/30',
    icon: Check,
    label: 'Good',
    description: 'Solid analysis with minor gaps'
  },
  C: {
    color: 'text-accent-yellow',
    bg: 'bg-accent-yellow/10',
    border: 'border-accent-yellow/30',
    icon: Info,
    label: 'Acceptable',
    description: 'Basic analysis, some limitations'
  },
  D: {
    color: 'text-orange-500',
    bg: 'bg-orange-500/10',
    border: 'border-orange-500/30',
    icon: AlertTriangle,
    label: 'Poor',
    description: 'Significant issues detected'
  },
  F: {
    color: 'text-accent-red',
    bg: 'bg-accent-red/10',
    border: 'border-accent-red/30',
    icon: X,
    label: 'Failed',
    description: 'Analysis failed or incomplete'
  }
}

export function QualityBadge({ 
  grade, 
  showDetails = false, 
  confidence,
  className 
}: QualityBadgeProps) {
  const config = gradeConfig[grade]
  const Icon = config.icon

  return (
    <div className={cn('inline-flex items-center gap-2', className)}>
      <div
        className={cn(
          'px-3 py-1.5 rounded-lg border flex items-center gap-2',
          config.bg,
          config.border
        )}
      >
        <Icon className={cn('w-4 h-4', config.color)} />
        <span className={cn('text-sm font-bold', config.color)}>
          Grade: {grade}
        </span>
      </div>

      {confidence !== undefined && (
        <div className="px-2 py-1.5 rounded-lg bg-bg-elevated border border-border-subtle">
          <span className="text-xs text-text-muted">
            Confidence: {Math.round(confidence * 100)}%
          </span>
        </div>
      )}

      {showDetails && (
        <div className={cn(
          'absolute z-10 p-3 rounded-lg card border max-w-xs',
          config.border
        )}>
          <p className={cn('text-sm font-semibold mb-1', config.color)}>
            {config.label}
          </p>
          <p className="text-xs text-text-muted">
            {config.description}
          </p>
        </div>
      )}
    </div>
  )
}
